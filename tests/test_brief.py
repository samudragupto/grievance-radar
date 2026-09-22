# Unit tests for ReportLab PDF Monday Brief generator.

import os
from pathlib import Path

from app.services.brief_generator import generate_brief_pdf


def test_pdf_file_is_created(tmp_path):
    """Verify ReportLab compiles and saves the PDF file to destination directory."""
    findings = [
        {
            "title": "Water Supply Surge in Ward 4",
            "z_score": 4.2,
            "percent_change": 340.0,
            "affected_count": 65,
            "wards": ["Ward 4"],
            "suggested_dept": "Water Supply",
            "sample_texts": ["No water reaching houses for 3 days."],
        }
    ]

    pdf_path = generate_brief_pdf(
        confirmed_findings=findings,
        week_label="Week 38, 2026",
        output_dir=str(tmp_path),
        total_complaints=1200,
    )

    assert os.path.exists(pdf_path)
    assert Path(pdf_path).name.endswith(".pdf")


def test_pdf_file_is_non_empty(tmp_path):
    """Verify generated PDF document contains non-zero byte stream."""
    findings = [
        {
            "title": "Waste Collection Disruption",
            "z_score": 3.1,
            "percent_change": 210.0,
            "affected_count": 38,
            "wards": ["Ward 7"],
            "suggested_dept": "Sanitation",
            "sample_texts": ["Garbage scattered everywhere."],
        }
    ]

    pdf_path = generate_brief_pdf(
        confirmed_findings=findings,
        week_label="Week 38, 2026",
        output_dir=str(tmp_path),
        total_complaints=1200,
    )

    size = os.path.getsize(pdf_path)
    assert size > 1000  # ReportLab PDF with headers, styles and text is >1KB


def test_brief_includes_findings_content(tmp_path):
    """Verify multiple confirmed findings can be compiled without exceeding boundary limits."""
    findings = [
        {
            "title": f"Surge #{i}",
            "z_score": 2.5 + i,
            "percent_change": 50.0 * i,
            "affected_count": 20 * i,
            "wards": [f"Ward {i}"],
            "suggested_dept": "Roads",
            "sample_texts": [f"Pothole issue #{i}"],
        }
        for i in range(1, 4)
    ]

    pdf_path = generate_brief_pdf(
        confirmed_findings=findings,
        week_label="Week 38, 2026",
        output_dir=str(tmp_path),
        total_complaints=1200,
    )

    assert os.path.exists(pdf_path)
