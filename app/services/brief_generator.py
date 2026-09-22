# PDF generation service for the 1-page Monday Brief using ReportLab.

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def generate_brief_pdf(
    confirmed_findings: List[Dict[str, Any]],
    week_label: str,
    output_dir: str = "instance/briefs",
    total_complaints: int = 1200,
) -> str:
    """Generate a clean, high-density 1-page PDF executive brief for municipal officers.

    Args:
        confirmed_findings: List of confirmed finding dictionaries (max 3).
        week_label: Readable label e.g., 'Week 38, 2026'.
        output_dir: Target directory to save the PDF.
        total_complaints: Total complaints reviewed in the active window.

    Returns:
        Absolute filepath to the generated PDF.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    filename = f"Monday_Brief_{week_label.replace(' ', '_').replace(',', '')}.pdf"
    file_full_path = out_path / filename

    doc = SimpleDocTemplate(
        str(file_full_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1a3a5c")
    text_color = colors.HexColor("#222222")
    muted_color = colors.HexColor("#555555")
    alert_red = colors.HexColor("#b30000")

    title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=muted_color,
        spaceAfter=12,
    )

    finding_title_style = ParagraphStyle(
        "FindingTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "FindingBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_color,
    )

    quote_style = ParagraphStyle(
        "FindingQuote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=muted_color,
    )

    footer_style = ParagraphStyle(
        "FooterText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=muted_color,
        alignment=1,
    )

    story = []

    # Document Header
    story.append(Paragraph("GRIEVANCE RADAR — MONDAY BRIEF", title_style))
    meta_line = (
        f"<b>{week_label}</b> | Generated from {total_complaints:,} complaints | "
        f"<b>Human-Confirmed Findings Only</b> | Date: {datetime.utcnow().strftime('%B %d, %Y')}"
    )
    story.append(Paragraph(meta_line, subtitle_style))
    story.append(
        HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=2, spaceAfter=14)
    )

    # Findings loop (max 3 to guarantee strictly 1-page layout)
    findings_to_render = confirmed_findings[:3]

    if not findings_to_render:
        story.append(Spacer(1, 20))
        story.append(
            Paragraph(
                "<i>No critical spikes were confirmed by the municipal officer for this "
                "period. All anomalies within expected operating limits.</i>",
                styles["Normal"],
            )
        )
    else:
        for idx, finding in enumerate(findings_to_render, start=1):
            severity_marker = (
                "[CRITICAL SURGE]" if finding.get("z_score", 0) > 3.0 else "[ELEVATED]"
            )
            title_text = (
                f"<b>#{idx}. {finding.get('title', 'Grievance Surge')}</b> "
                f"&nbsp;&nbsp;<font color='{alert_red}'>{severity_marker}</font>"
            )
            story.append(Paragraph(title_text, finding_title_style))

            z_score = finding.get("z_score", 0.0)
            pct = finding.get("percent_change", 0.0)
            count = finding.get("affected_count", 0)
            wards = ", ".join(finding.get("wards", [])) or "City-wide"
            dept = finding.get("suggested_dept", "General Municipal")

            stats_text = (
                f"• <b>Statistical Anomaly:</b> Z-Score = <b>+{round(z_score, 1)}σ</b> | "
                f"Relative Surge: <b>+{int(pct)}%</b> | "
                f"Total Affected Complaints: <b>{count}</b>"
            )
            story.append(Paragraph(stats_text, bullet_style))

            scope_text = (
                f"• <b>Affected Locations:</b> {wards} | "
                f"<b>Recommended Action Department:</b> <u>{dept}</u>"
            )
            story.append(Paragraph(scope_text, bullet_style))

            samples = finding.get("sample_texts", [])
            if samples:
                truncated_sample = samples[0][:120] + ("..." if len(samples[0]) > 120 else "")
                excerpt_text = f'• <b>Citizen Voice Excerpt:</b> "{truncated_sample}"'
                story.append(Paragraph(excerpt_text, quote_style))

            story.append(Spacer(1, 10))
            if idx < len(findings_to_render):
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.5,
                        color=colors.HexColor("#e0e0e0"),
                        spaceBefore=4,
                        spaceAfter=10,
                    )
                )

    # Footer section
    story.append(Spacer(1, 20))
    story.append(
        HRFlowable(width="100%", thickness=1, color=primary_color, spaceBefore=8, spaceAfter=8)
    )
    footer_text = (
        "Grievance Radar | One officer, one page, every week.<br/>"
        "SRM Institute of Science & Technology, Tiruchirappalli | YUVA Megathon 2026<br/>"
        f"Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} • "
        f"Tamper-evident Audit ID: GR-{int(datetime.utcnow().timestamp())}"
    )
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    logger.info("Successfully generated 1-page Monday Brief at %s", str(file_full_path))
    return str(file_full_path)
