# Brief preview and PDF download routes.

import logging
from pathlib import Path
from flask import Blueprint, abort, current_app, render_template, send_file
from app.models import Brief, Finding

logger = logging.getLogger(__name__)
brief_bp = Blueprint("brief", __name__, url_prefix="/brief")


@brief_bp.route("/preview")
def preview():
    """Render HTML preview of the Monday Brief using currently confirmed findings."""
    confirmed_findings = Finding.query.filter_by(status="confirmed").order_by(Finding.z_score.desc()).all()
    latest_brief = Brief.query.order_by(Brief.generated_at.desc()).first()

    return render_template(
        "brief_preview.html",
        confirmed_findings=confirmed_findings,
        latest_brief=latest_brief,
    )


@brief_bp.route("/download/<int:brief_id>")
def download(brief_id: int):
    """Serve the generated PDF document for download.

    Args:
        brief_id: Primary key ID of the Brief record.
    """
    brief = Brief.query.get(brief_id)
    if not brief or not brief.pdf_path:
        abort(404, description="Brief not found or PDF path missing.")

    pdf_file = Path(brief.pdf_path)
    if not pdf_file.exists():
        abort(404, description="PDF file does not exist on server storage.")

    logger.info("Serving PDF brief #%d: %s", brief_id, str(pdf_file))
    return send_file(
        str(pdf_file),
        as_attachment=True,
        download_name=pdf_file.name,
        mimetype="application/pdf",
    )
