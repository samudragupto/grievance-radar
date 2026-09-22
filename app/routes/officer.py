# Officer dashboard routes for human-in-the-loop decision making.

from datetime import datetime
import json
import logging
from flask import Blueprint, jsonify, render_template, request
from app.database import db
from app.models import Brief, Cluster, Complaint, Finding, OfficerDecision
from app.services.brief_generator import generate_brief_pdf

logger = logging.getLogger(__name__)
officer_bp = Blueprint("officer", __name__, url_prefix="/officer")


@officer_bp.route("/dashboard")
def dashboard():
    """Render officer decision dashboard showing pending anomaly findings."""
    pending_findings = Finding.query.filter_by(status="pending").order_by(Finding.z_score.desc()).all()
    confirmed_findings = Finding.query.filter_by(status="confirmed").order_by(Finding.decided_at.desc()).all()
    dismissed_findings = Finding.query.filter_by(status="dismissed").order_by(Finding.decided_at.desc()).all()

    total_complaints = Complaint.query.count()
    cluster_count = Cluster.query.count()

    return render_template(
        "dashboard.html",
        pending_findings=pending_findings,
        confirmed_findings=confirmed_findings,
        dismissed_findings=dismissed_findings,
        total_complaints=total_complaints,
        cluster_count=cluster_count,
        pending_count=len(pending_findings),
        confirmed_count=len(confirmed_findings),
        dismissed_count=len(dismissed_findings),
    )


@officer_bp.route("/decision", methods=["POST"])
def record_decision():
    """Process human officer decision: confirm, dismiss, or edit an automated finding."""
    data = request.get_json() or {}
    finding_id = data.get("finding_id")
    action = data.get("action")
    edited_title = data.get("edited_title")
    edited_dept = data.get("edited_dept")

    if not finding_id or action not in ["confirm", "dismiss", "edit"]:
        return jsonify({"error": "Invalid payload. finding_id and valid action required."}), 400

    finding = Finding.query.get(finding_id)
    if not finding:
        return jsonify({"error": f"Finding with id {finding_id} not found."}), 404

    # Apply officer decision
    now = datetime.utcnow()
    if action == "confirm":
        finding.status = "confirmed"
    elif action == "dismiss":
        finding.status = "dismissed"
    elif action == "edit":
        if edited_title:
            finding.title = edited_title
        if edited_dept:
            finding.suggested_dept = edited_dept
        finding.status = "confirmed"

    finding.decided_at = now

    decision = OfficerDecision(
        finding_id=finding.id,
        action=action,
        edited_title=edited_title,
        edited_dept=edited_dept,
        decided_at=now,
    )
    db.session.add(decision)
    db.session.commit()

    logger.info("Officer applied '%s' on Finding #%d", action, finding.id)
    return jsonify({
        "success": True,
        "finding": finding.to_dict(),
        "message": f"Finding #{finding.id} successfully {finding.status}.",
    })


@officer_bp.route("/history")
def history():
    """Return transparent audit trail of all officer decisions."""
    decisions = OfficerDecision.query.order_by(OfficerDecision.decided_at.desc()).all()
    return jsonify([d.to_dict() for d in decisions])
