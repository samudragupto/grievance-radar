# REST API endpoints for upload, pipeline orchestration, clusters, findings, and trends.

import json
import logging
from datetime import datetime

import pandas as pd
from flask import Blueprint, current_app, jsonify, request

from app.database import db
from app.models import Brief, Cluster, Complaint, Finding
from app.services.analyze import compute_rolling_baseline, detect_spikes, rank_findings
from app.services.brief_generator import generate_brief_pdf
from app.services.cluster import cluster_complaints
from app.services.embed import generate_embeddings
from app.services.upload import save_and_parse_upload

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/upload", methods=["POST"])
def upload_file():
    """Accept and ingest complaint dataset (CSV or JSON)."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in form data."}), 400

    file_obj = request.files["file"]
    try:
        records = save_and_parse_upload(file_obj)
    except Exception as e:
        logger.error("Upload parsing failed: %s", e)
        return jsonify({"error": str(e)}), 400

    imported = 0
    skipped = 0
    for item in records:
        try:
            filed_d = datetime.strptime(item["filed_date"], "%Y-%m-%d").date()
            complaint = Complaint(
                text=item["text"],
                category=item.get("category"),
                ward=item["ward"],
                department=item.get("department"),
                filed_date=filed_d,
                is_synthetic=item.get("is_synthetic", True),
            )
            db.session.add(complaint)
            imported += 1
        except Exception:
            skipped += 1

    db.session.commit()
    logger.info("Imported %d complaints (%d skipped)", imported, skipped)
    return jsonify({"imported": imported, "skipped": skipped})


@api_bp.route("/pipeline", methods=["POST"])
def trigger_pipeline():
    """Execute end-to-end analytics pipeline: embed -> cluster -> analyze -> store findings."""
    complaints = Complaint.query.all()
    if not complaints:
        return jsonify({"error": "No complaints available. Please upload data first."}), 400

    texts = [c.text for c in complaints]
    complaint_dicts = [c.to_dict() for c in complaints]

    # Stage 1: Embeddings
    algo = current_app.config.get("CLUSTERING_ALGO", "bertopic")
    embeddings = generate_embeddings(texts)

    # Stage 2: Clustering
    cluster_results = cluster_complaints(embeddings, texts, algo=algo)
    labels = cluster_results.get("labels", [])
    topic_labels = cluster_results.get("topic_labels", {})

    # Clear prior clusters and save new ones
    Cluster.query.delete()
    Finding.query.delete()
    db.session.commit()

    cluster_id_map = {}
    for c_info in cluster_results.get("clusters", []):
        c_id = c_info["id"]
        label = c_info["label"]
        cluster_rec = Cluster(id=c_id, label=label, count=c_info["count"])
        db.session.add(cluster_rec)
        cluster_id_map[c_id] = cluster_rec

    db.session.commit()

    # Assign cluster IDs back to complaints
    for i, c in enumerate(complaints):
        if i < len(labels):
            c.cluster_id = int(labels[i])
            c.embedded = True
            complaint_dicts[i]["cluster_id"] = int(labels[i])

    db.session.commit()

    # Stage 3: Statistical Baseline & Spike Detection
    rolling_weeks = current_app.config.get("ROLLING_WEEKS", 4)
    z_thresh = current_app.config.get("ZSCORE_THRESHOLD", 2.5)
    pct_thresh = current_app.config.get("PERCENT_CHANGE_THRESHOLD", 50.0)
    max_findings = current_app.config.get("MAX_FINDINGS", 3)

    baseline = compute_rolling_baseline(complaint_dicts, window_weeks=rolling_weeks)
    spikes = detect_spikes(
        complaint_dicts,
        baseline,
        z_thresh=z_thresh,
        pct_thresh=pct_thresh,
        cluster_labels=topic_labels,
    )
    top_findings = rank_findings(spikes, top_n=max_findings)

    saved_findings = []
    for f in top_findings:
        finding_rec = Finding(
            cluster_id=f.get("cluster_id"),
            title=f["title"],
            z_score=f["z_score"],
            percent_change=f["percent_change"],
            affected_count=f["affected_count"],
            wards=json.dumps(f["wards"]),
            suggested_dept=f["suggested_dept"],
            sample_texts=json.dumps(f["sample_texts"]),
            status="pending",
        )
        db.session.add(finding_rec)
        saved_findings.append(finding_rec)

    db.session.commit()

    return jsonify(
        {
            "success": True,
            "clusters_found": len(cluster_results.get("clusters", [])),
            "spikes_detected": len(spikes),
            "top_findings": [f.to_dict() for f in saved_findings],
        }
    )


@api_bp.route("/clusters", methods=["GET"])
def get_clusters():
    """Return all discovered grievance clusters."""
    clusters = Cluster.query.order_by(Cluster.count.desc()).all()
    return jsonify([c.to_dict() for c in clusters])


@api_bp.route("/findings", methods=["GET"])
def get_findings():
    """Return findings filtered by optional status query param."""
    status = request.args.get("status")
    query = Finding.query
    if status:
        query = query.filter_by(status=status)
    findings = query.order_by(Finding.z_score.desc()).all()
    return jsonify([f.to_dict() for f in findings])


@api_bp.route("/brief", methods=["POST"])
def generate_brief():
    """Generate official Monday Brief PDF from confirmed findings."""
    confirmed = Finding.query.filter_by(status="confirmed").order_by(Finding.z_score.desc()).all()
    if not confirmed:
        return jsonify({"error": "No confirmed findings available to generate brief."}), 400

    confirmed_dicts = [f.to_dict() for f in confirmed]
    week_label = f"Week {datetime.utcnow().isocalendar()[1]}, {datetime.utcnow().year}"
    briefs_dir = str(current_app.config.get("BRIEFS_DIR"))

    pdf_path = generate_brief_pdf(
        confirmed_findings=confirmed_dicts,
        week_label=week_label,
        output_dir=briefs_dir,
        total_complaints=Complaint.query.count(),
    )

    brief_rec = Brief(
        week_label=week_label,
        findings=json.dumps([f.id for f in confirmed]),
        pdf_path=pdf_path,
    )
    db.session.add(brief_rec)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "brief_id": brief_rec.id,
            "week_label": week_label,
            "download_url": f"/brief/download/{brief_rec.id}",
        }
    )


@api_bp.route("/trends", methods=["GET"])
def get_trends():
    """Return anonymized aggregated statistics for public trends (no PII, no raw text)."""
    complaints = Complaint.query.all()
    if not complaints:
        return jsonify(
            {
                "weekly_categories": [],
                "ward_counts": [],
                "top_categories": [],
                "ward_coordinates": [],
            }
        )

    data = [
        {
            "ward": c.ward,
            "department": c.department or "General",
            "filed_date": c.filed_date.isoformat(),
        }
        for c in complaints
    ]
    df = pd.DataFrame(data)
    df["filed_date"] = pd.to_datetime(df["filed_date"])
    df["week"] = df["filed_date"].dt.strftime("%Y-W%W")

    # Category counts over time
    top_depts = df["department"].value_counts().head(5).index.tolist()
    weekly_cat = (
        df[df["department"].isin(top_depts)]
        .groupby(["week", "department"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Ward counts
    ward_counts = df["ward"].value_counts().reset_index()
    ward_counts.columns = ["ward", "count"]

    # Realistic Tamil Nadu / Tiruchirappalli coordinates for demo Wards 1 to 12
    coords_map = {
        "Ward 1": [10.8250, 78.6900],
        "Ward 2": [10.8300, 78.6980],
        "Ward 3": [10.8190, 78.6850],
        "Ward 4": [10.8350, 78.7050],  # Primary spike ward
        "Ward 5": [10.8400, 78.6920],
        "Ward 6": [10.8120, 78.6780],
        "Ward 7": [10.8050, 78.6990],
        "Ward 8": [10.8450, 78.7150],
        "Ward 9": [10.8280, 78.7200],
        "Ward 10": [10.8150, 78.7100],
        "Ward 11": [10.8000, 78.6880],
        "Ward 12": [10.8500, 78.6800],
    }

    ward_geo = []
    for _, r in ward_counts.iterrows():
        w_name = r["ward"]
        cnt = int(r["count"])
        lat_lon = coords_map.get(w_name, [10.8250, 78.6900])
        ward_geo.append(
            {
                "ward": w_name,
                "count": cnt,
                "lat": lat_lon[0],
                "lng": lat_lon[1],
            }
        )

    return jsonify(
        {
            "weeks": weekly_cat["week"].tolist() if "week" in weekly_cat else [],
            "categories": {col: weekly_cat[col].tolist() for col in top_depts if col in weekly_cat},
            "ward_counts": ward_counts.to_dict(orient="records"),
            "ward_geo": ward_geo,
        }
    )
