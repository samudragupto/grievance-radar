# Main public and navigation routes.

from flask import Blueprint, jsonify, render_template

from app.database import db
from app.models import Brief, Cluster, Complaint, Finding

main_bp = Blueprint("main", __name__)


@main_bp.route("/health")
def health():
    """Liveness/readiness probe used by container orchestrators and the CD smoke test.

    Returns HTTP 200 with basic runtime counts when the application and its
    database are reachable, otherwise HTTP 503. Deliberately exposes no
    complaint text or personal data.
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        payload = {
            "status": "ok",
            "complaints": Complaint.query.count(),
            "clusters": Cluster.query.count(),
            "pending_findings": Finding.query.filter_by(status="pending").count(),
            "briefs": Brief.query.count(),
        }
    except Exception as exc:  # pragma: no cover - exercised only on DB outage
        db.session.rollback()
        return jsonify({"status": "unhealthy", "error": str(exc)}), 503

    return jsonify(payload)


@main_bp.route("/")
def index():
    """Render landing page with file upload and live stats summary."""
    total_complaints = Complaint.query.count()
    total_clusters = Cluster.query.count()
    pending_findings = Finding.query.filter_by(status="pending").count()
    latest_brief = Brief.query.order_by(Brief.generated_at.desc()).first()

    return render_template(
        "index.html",
        total_complaints=total_complaints,
        total_clusters=total_clusters,
        pending_findings=pending_findings,
        latest_brief=latest_brief,
    )


@main_bp.route("/trends")
def trends():
    """Render public anonymized analytics view with charts and geospatial maps."""
    return render_template("trends.html")


@main_bp.route("/clusters")
def clusters():
    """Render cluster visualization view."""
    all_clusters = Cluster.query.order_by(Cluster.count.desc()).all()
    return render_template("clusters.html", clusters=all_clusters)
