"""
report_generator.py — ReportLab PDF rendering for maintenance reports.

Design decisions:
  - create_pdf(report, inspection_record) accepts the inspection record
    dict so it can derive a unique, deterministic filename itself.
    This removes the caller's responsibility for path management.
  - All dynamic text is passed through _safe() which escapes XML/HTML
    special characters (&, <, >, ", ') before reaching ReportLab's
    Paragraph parser.  Failure to do this causes ReportLab to raise
    cryptic XML errors when machine notes contain ampersands, etc.
  - REPORTS_DIR is read from config.py (single source of truth).
  - Returns the absolute path to the saved file so callers can open
    it for download without reconstructing the path.
"""

import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import REPORTS_DIR


# ------------------------------------------------------------------
# ReportLab style constants
# ------------------------------------------------------------------
_styles = getSampleStyleSheet()

title_style = _styles["Heading1"]
title_style.alignment = TA_CENTER
title_style.textColor = HexColor("#003366")

heading_style = _styles["Heading2"]
heading_style.textColor = HexColor("#003366")

body_style = _styles["BodyText"]


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _safe(value: object) -> str:
    """
    Convert *value* to a string and escape XML/HTML special characters
    so ReportLab's Paragraph XML parser does not raise errors on input
    that contains  &  <  >  "  '  (all common in maintenance notes).
    """
    return escape(str(value) if value is not None else "")


def _build_filename(inspection_record: dict) -> str:
    """Derive a unique, filesystem-safe PDF filename from the record."""
    machine_id = (
        str(inspection_record.get("selected_machine", "machine"))
        .replace("/", "-")
        .replace("\\", "-")
        .strip()
    )
    date_str = str(
        inspection_record.get(
            "inspection_date",
            datetime.now().strftime("%Y-%m-%d"),
        )
    )
    return os.path.join(REPORTS_DIR, f"report_{machine_id}_{date_str}.pdf")


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------

def create_pdf(report: dict, inspection_record: dict) -> str:
    """
    Render a PDF maintenance report and save it to REPORTS_DIR.

    Parameters
    ----------
    report : dict
        Validated AI-generated report dict (from llm.generate_report).
    inspection_record : dict
        Original inspection record used to build the output filename.

    Returns
    -------
    str
        Absolute path to the saved PDF file.

    Raises
    ------
    Exception
        Propagates any ReportLab error so the caller can surface it.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = _build_filename(inspection_record)

    pdf = SimpleDocTemplate(
        filename,
        pagesize=(8.27 * inch, 11.69 * inch),   # A4
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    elements = []

    # -------------------------
    # Title
    # -------------------------
    elements.append(
        Paragraph("<b>FIELD MAINTENANCE REPORT</b>", title_style)
    )
    elements.append(Spacer(1, 20))

    # -------------------------
    # Asset Information Table
    # -------------------------
    table_data = [
        ["Asset ID",        _safe(report.get("asset_id", ""))],
        ["Inspection Date", _safe(report.get("inspection_date", ""))],
        ["Technician",      _safe(report.get("technician", ""))],
        ["Status",          _safe(report.get("current_machine_status", ""))],
    ]

    table = Table(table_data, colWidths=[2.2 * inch, 4.3 * inch])
    table.setStyle(
        TableStyle([
            ("BACKGROUND",    (0, 0), (0, -1), HexColor("#E8F1FF")),
            ("TEXTCOLOR",     (0, 0), (-1, -1), HexColor("#000000")),
            ("GRID",          (0, 0), (-1, -1), 0.5, HexColor("#A0A0A0")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 18))

    # -------------------------
    # Reported Issue
    # -------------------------
    elements.append(Paragraph("<b>Reported Issue</b>", heading_style))
    elements.append(
        Paragraph(_safe(report.get("reported_issue", "")), body_style)
    )
    elements.append(Spacer(1, 14))

    # -------------------------
    # Maintenance Summary
    # -------------------------
    elements.append(Paragraph("<b>Maintenance Summary</b>", heading_style))
    elements.append(
        Paragraph(_safe(report.get("maintenance_summary", "")), body_style)
    )
    elements.append(Spacer(1, 14))

    # -------------------------
    # Image Observations
    # -------------------------
    elements.append(Paragraph("<b>Image Observations</b>", heading_style))
    elements.append(
        Paragraph(_safe(report.get("image_observations", "")), body_style)
    )
    elements.append(Spacer(1, 14))

    # -------------------------
    # Recommendations
    # -------------------------
    elements.append(Paragraph("<b>Recommendations</b>", heading_style))

    recommendations = report.get("recommendations", [])
    if isinstance(recommendations, list) and recommendations:
        for item in recommendations:
            elements.append(Paragraph(f"• {_safe(item)}", body_style))
    else:
        elements.append(
            Paragraph("No specific recommendations provided.", body_style)
        )

    elements.append(Spacer(1, 30))

    # -------------------------
    # Footer
    # -------------------------
    elements.append(
        Paragraph(
            "<font size=9 color='grey'>"
            "This report was automatically generated using AI based on "
            "technician notes and the uploaded machine photograph."
            "</font>",
            body_style,
        )
    )

    pdf.build(elements)
    return filename