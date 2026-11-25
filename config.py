"""
config.py — Centralized project configuration.

Import this module wherever you need file paths, CSV column names,
date formats, or AI-related constants. Never hard-code these values
in individual files.
"""

import os

# ------------------------------------------------------------------
# Base directory (project root — same folder as this file)
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------
# File paths
# ------------------------------------------------------------------
CSV_PATH    = os.path.join(BASE_DIR, "data", "maintenance.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "report_prompt.txt")


# ------------------------------------------------------------------
# CSV column names (actual headers in maintenance.csv)
# ------------------------------------------------------------------
COL_MACH  = "mach"
COL_DATE  = "date_received"
COL_ISSUE = "issue"
COL_INFO  = "info"
COL_TECH  = "tech"

REQUIRED_COLUMNS = [COL_MACH, COL_DATE, COL_ISSUE, COL_INFO, COL_TECH]


# ------------------------------------------------------------------
# Date format used in the CSV  →  DD/MM/YYYY  (e.g. 04/03/2015)
# ------------------------------------------------------------------
CSV_DATE_FORMAT = "%d/%m/%Y"


# ------------------------------------------------------------------
# Gemini / AI settings
# ------------------------------------------------------------------
GEMINI_MODEL = "gemini-2.5-flash-lite"

# Keys that the AI is responsible for populating.
# Metadata keys (asset_id, inspection_date, technician, reported_issue)
# are ALWAYS overwritten from the official record after AI response.
GEMINI_REQUIRED_KEYS = [
    "maintenance_summary",
    "image_observations",
    "current_machine_status",
    "recommendations",
]

VALID_MACHINE_STATUSES = {
    "Operational",
    "Maintenance Required",
    "Requires Further Inspection",
}
