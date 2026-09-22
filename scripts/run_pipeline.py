# Command-line interface to execute the full analytics pipeline.

import argparse
import json
import logging
import time

from app import create_app
from app.database import db
from app.models import Cluster, Complaint, Finding
from app.services.analyze import compute_rolling_baseline, detect_spikes, rank_findings
from app.services.cluster import cluster_complaints
from app.services.embed import generate_embeddings
from app.services.preprocess import load_and_anonymize

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("run_pipeline")


def run(input_path: str):
    """Execute data ingestion, embedding, clustering, spike analysis, and database storage.

    Args:
        input_path: Path to raw input CSV or JSON complaint file.
    """
    app = create_app("development")
    with app.app_context():
        # Step 1: Load and Anonymize
        start_time = time.time()
        records = load_and_anonymize(input_path)
        logger.info("Loaded %d complaints in %.1fs", len(records), time.time() - start_time)

        # Clear existing DB data
        Complaint.query.delete()
        Cluster.query.delete()
        Finding.query.delete()
        db.session.commit()

        for item in records:
            from datetime import datetime

            c = Complaint(
                text=item["text"],
                category=item.get("category"),
                ward=item["ward"],
                department=item.get("department"),
                filed_date=datetime.strptime(item["filed_date"], "%Y-%m-%d").date(),
                is_synthetic=item.get("is_synthetic", True),
            )
            db.session.add(c)
        db.session.commit()

        texts = [r["text"] for r in records]

        # Step 2: Embeddings
        t_embed_start = time.time()
        embeddings = generate_embeddings(texts)
        t_embed = time.time() - t_embed_start
        logger.info("Generated %d embeddings (384-dim) in %.1fs", len(embeddings), t_embed)

        # Step 3: Clustering
        t_cluster_start = time.time()
        cluster_results = cluster_complaints(embeddings, texts, algo="kmeans")
        t_cluster = time.time() - t_cluster_start
        clusters_found = cluster_results.get("clusters", [])
        labels = cluster_results.get("labels", [])
        topic_labels = cluster_results.get("topic_labels", {})
        logger.info("Clustered into %d groups in %.1fs", len(clusters_found), t_cluster)

        # Save clusters
        complaints_in_db = Complaint.query.all()
        for idx, comp in enumerate(complaints_in_db):
            if idx < len(labels):
                comp.cluster_id = int(labels[idx])
                comp.embedded = True
                records[idx]["cluster_id"] = int(labels[idx])

        for c_info in clusters_found:
            db.session.add(Cluster(id=c_info["id"], label=c_info["label"], count=c_info["count"]))
        db.session.commit()

        # Step 4: Baseline and Spike Detection
        baseline = compute_rolling_baseline(records, window_weeks=4)
        spikes = detect_spikes(
            records,
            baseline,
            z_thresh=2.5,
            pct_thresh=50.0,
            cluster_labels=topic_labels,
        )
        logger.info("Detected %d spikes", len(spikes))

        # Step 5: Rank top findings
        top_findings = rank_findings(spikes, top_n=3)
        for idx, f in enumerate(top_findings, 1):
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
            logger.info(
                "  [%d] %s | Z-score: +%.1fσ | Affected: %d complaints",
                idx,
                f["title"],
                f["z_score"],
                f["affected_count"],
            )

        db.session.commit()
        logger.info("Results successfully saved to SQLite database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Grievance Radar analytics pipeline.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/sample_complaints.json",
        help="Path to input complaints file.",
    )
    args = parser.parse_args()
    run(args.input)
