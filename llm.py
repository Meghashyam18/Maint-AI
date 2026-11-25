"""
llm.py — Gemini AI integration for maintenance report generation.

Design decisions:
  - Prompt is loaded from the versioned file in prompts/report_prompt.txt.
  - AI is instructed NOT to supply metadata fields; they are always
    overwritten here from the authoritative inspection record.
  - Strict schema validation rejects malformed responses before they
    can reach the PDF renderer.
  - Gemini and JSON errors are converted to descriptive exceptions so
    the caller (new_inspection.py) can show a friendly error message.
"""

import json
import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError
from PIL import Image

from config import (
    GEMINI_MODEL,
    GEMINI_REQUIRED_KEYS,
    PROMPT_PATH,
    VALID_MACHINE_STATUSES,
)

load_dotenv()

logger = logging.getLogger(__name__)

# Initialise Gemini client once at module load
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ------------------------------------------------------------------
# PROMPT LOADER
# ------------------------------------------------------------------

def _load_prompt_template() -> str:
    """
    Load the versioned AI prompt template from the prompts directory.

    Raises
    ------
    FileNotFoundError
        When report_prompt.txt is missing.
    """
    try:
        with open(PROMPT_PATH, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"AI prompt file not found at '{PROMPT_PATH}'. "
            "Ensure 'prompts/report_prompt.txt' exists in the project root."
        )


# ------------------------------------------------------------------
# SCHEMA VALIDATION
# ------------------------------------------------------------------

def _validate_schema(data: dict) -> None:
    """
    Validate that the Gemini JSON response contains all required keys
    and that controlled-vocabulary fields carry valid values.

    Raises
    ------
    ValueError
        With a descriptive message on any schema violation.
    """
    # Required keys
    missing = [k for k in GEMINI_REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(
            f"Gemini response is missing required fields: {missing}"
        )

    # Controlled vocabulary: current_machine_status
    status = str(data.get("current_machine_status", "")).strip()
    if status not in VALID_MACHINE_STATUSES:
        raise ValueError(
            f"Invalid 'current_machine_status' value: '{status}'. "
            f"Must be exactly one of: {sorted(VALID_MACHINE_STATUSES)}"
        )

    # recommendations must be a non-empty list
    recs = data.get("recommendations")
    if not isinstance(recs, list) or len(recs) == 0:
        raise ValueError(
            "'recommendations' must be a non-empty JSON array of strings."
        )

    # Non-empty AI sections
    if not str(data.get("maintenance_summary", "")).strip():
        raise ValueError("'maintenance_summary' must not be empty.")

    if not str(data.get("image_observations", "")).strip():
        raise ValueError("'image_observations' must not be empty.")


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------

def generate_report(record: dict, image: Image.Image | None = None) -> dict:
    """
    Generate a validated maintenance report via the Gemini API.

    The prompt is loaded from ``prompts/report_prompt.txt`` (version-
    controlled separately from this code).  After receiving the AI
    response, all metadata fields (asset_id, inspection_date,
    technician, reported_issue) are overwritten with authoritative
    values from *record* — the AI is never trusted to supply these.

    Parameters
    ----------
    record : dict
        Inspection record.  Expected keys:
        ``selected_machine``, ``inspection_date``, ``reported_issue``,
        ``technician_display_name``, ``inspection_summary``.
    image : PIL.Image.Image
        Machine photograph to be analysed.

    Returns
    -------
    dict
        Validated report with all metadata populated from *record*.

    Raises
    ------
    FileNotFoundError
        When the prompt template file is missing.
    RuntimeError
        When the Gemini API call itself fails.
    ValueError
        When the AI returns non-JSON output or fails schema validation.
    """
    # --- Build prompt from versioned template ---
    template = _load_prompt_template()
    photograph_note = (
        "Attached to this message — please analyse it."
        if image is not None
        else "NOT PROVIDED — set image_observations to exactly: "
             "'No photograph was provided for this inspection.'"
    )
    prompt = template.format(
        inspection_date=record.get("inspection_date", "Not provided"),
        reported_issue=record.get("reported_issue", "Not provided"),
        inspection_summary=record.get("inspection_summary", "Not provided"),
        photograph_note=photograph_note,
    )

    # Build Gemini contents: always include prompt, add image only when present
    gemini_contents: list = [prompt]
    if image is not None:
        gemini_contents.append(image)

    # --- Call Gemini (with retry for transient network drops) ---
    _MAX_RETRIES = 3
    _RETRY_DELAY = 2   # seconds between attempts

    last_exc: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=gemini_contents,
            )
            break   # success — exit retry loop
        except Exception as exc:
            last_exc = exc
            err_str = str(exc).lower()

            # Handle explicit Gemini server-side availability errors
            if isinstance(exc, ServerError):
                logger.error("Gemini service unavailable (ServerError): %s", exc)
                raise RuntimeError(
                    "The AI service is temporarily unavailable. "
                    "Please try again later."
                ) from exc

            # Retry only on transient network/connection errors
            is_transient = any(
                marker in err_str
                for marker in (
                    "10054",          # WinError: connection forcibly closed
                    "readerror",
                    "connectionerror",
                    "timeout",
                    "remotedisconnected",
                    "read error",
                    "connection reset",
                )
            )

            if is_transient and attempt < _MAX_RETRIES:
                import time
                logger.warning(
                    "Gemini connection error (attempt %d/%d), retrying in %ds: %s",
                    attempt, _MAX_RETRIES, _RETRY_DELAY, exc,
                )
                time.sleep(_RETRY_DELAY)
                continue

            # Non-transient error or out of retries — give up
            logger.error("Gemini API call failed: %s", exc, exc_info=True)
            raise RuntimeError(
                f"The AI service returned an error after {attempt} attempt(s). "
                f"Please check your network connection and try again. "
                f"Detail: {exc}"
            ) from exc

    raw_text = (response.text or "").strip()

    # Strip markdown code fences if the model added them despite instructions
    if raw_text.startswith("```"):
        raw_text = (
            raw_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

    # --- Parse JSON ---
    try:
        report = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error(
            "Gemini returned non-JSON output (first 500 chars):\n%s",
            raw_text[:500],
        )
        raise ValueError(
            "The AI returned a response that could not be parsed as JSON. "
            f"Parse error: {exc}"
        ) from exc

    # --- Schema validation ---
    _validate_schema(report)

    # --- Overwrite metadata with authoritative record values ---
    # The AI is explicitly instructed not to populate these fields,
    # but we enforce it here regardless of what the model returned.
    report["asset_id"]        = str(record.get("selected_machine", ""))
    report["inspection_date"] = str(record.get("inspection_date", ""))
    report["technician"]      = str(record.get("technician_display_name", ""))
    report["reported_issue"]  = str(record.get("reported_issue", "Not available"))

    # --- Override image_observations when no photo was provided ---
    # This is a belt-and-braces guard: the prompt already instructs the AI
    # to set this field, but we enforce the correct value here too.
    if image is None:
        report["image_observations"] = (
            "No photograph was provided for this inspection."
        )

    return report