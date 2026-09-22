# Statistical analysis, rolling baseline calculation, and Z-score spike detection.

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_rolling_baseline(
    complaints: List[Dict[str, Any]],
    window_weeks: int = 4,
) -> Dict[str, Dict[str, float]]:
    """Compute rolling baseline mean and standard deviation over historical weeks.

    Complaints are grouped by (cluster_id, ward).

    Args:
        complaints: List of complaint dictionary records.
        window_weeks: Number of historical weeks to average.

    Returns:
        Dictionary keyed by "cluster_id::ward" pointing to {"mean": float, "std": float}.
    """
    if not complaints:
        return {}

    df = pd.DataFrame(complaints)
    if "filed_date" not in df.columns or "cluster_id" not in df.columns:
        return {}

    df["filed_date"] = pd.to_datetime(df["filed_date"])
    # Convert to weekly periods (year-week)
    df["week"] = df["filed_date"].dt.to_period("W")

    max_week = df["week"].max()
    # Baseline covers window prior to the latest active week
    baseline_df = df[df["week"] < max_week]

    if baseline_df.empty:
        baseline_df = df

    baseline_stats: Dict[str, Dict[str, float]] = {}

    # Weekly count by group
    grouped = (
        baseline_df.groupby(["cluster_id", "ward", "week"])
        .size()
        .reset_index(name="count")
    )

    for (c_id, ward), group in grouped.groupby(["cluster_id", "ward"]):
        counts = group["count"].values
        # Pad with zeros if fewer historical weeks recorded than window
        if len(counts) < window_weeks:
            counts = np.pad(counts, (window_weeks - len(counts), 0), "constant")
        else:
            counts = counts[-window_weeks:]

        mean = float(np.mean(counts))
        std = float(np.std(counts, ddof=1)) if len(counts) > 1 else 0.0
        baseline_stats[f"{c_id}::{ward}"] = {"mean": mean, "std": std}

    return baseline_stats


def detect_spikes(
    complaints: List[Dict[str, Any]],
    baseline: Dict[str, Dict[str, float]],
    z_thresh: float = 2.5,
    pct_thresh: float = 50.0,
    cluster_labels: Dict[int, str] = None,
) -> List[Dict[str, Any]]:
    """Detect statistical anomalies where current complaints deviate significantly from baseline.

    Args:
        complaints: All complaints including the current week.
        baseline: Baseline stats per cluster_id::ward key.
        z_thresh: Minimum Z-score to classify as a spike.
        pct_thresh: Minimum percentage increase relative to baseline.
        cluster_labels: Mapping of cluster IDs to readable titles.

    Returns:
        List of flagged spike finding dictionaries sorted descending by severity_score.
    """
    if not complaints:
        return []

    cluster_labels = cluster_labels or {}
    df = pd.DataFrame(complaints)
    df["filed_date"] = pd.to_datetime(df["filed_date"])
    df["week"] = df["filed_date"].dt.to_period("W")
    max_week = df["week"].max()

    current_week_df = df[df["week"] == max_week]
    if current_week_df.empty:
        current_week_df = df

    current_counts = (
        current_week_df.groupby(["cluster_id", "ward", "department"])
        .agg(
            count=("text", "count"),
            sample_texts=("text", lambda s: list(s.head(3))),
        )
        .reset_index()
    )

    spikes: List[Dict[str, Any]] = []

    for _, row in current_counts.iterrows():
        c_id = row["cluster_id"]
        ward = str(row["ward"])
        dept = str(row["department"])
        cur_count = int(row["count"])
        samples = row["sample_texts"]

        key = f"{c_id}::{ward}"
        base = baseline.get(key, {"mean": max(1.0, cur_count * 0.3), "std": 1.0})
        mean = base["mean"]
        std = base["std"]

        # Calculate Z-score
        z = (cur_count - mean) / std if std > 0.05 else (cur_count - mean) / 1.0
        pct_change = ((cur_count - mean) / mean) * 100.0 if mean > 0 else 100.0

        if z >= z_thresh and pct_change >= pct_thresh:
            cluster_name = cluster_labels.get(c_id, f"Grievance Cluster {c_id}")
            title = f"{dept} surge in {ward} (+{int(pct_change)}%, z={round(z, 1)})"

            severity_score = float(z * cur_count)

            spikes.append(
                {
                    "cluster_id": int(c_id) if pd.notnull(c_id) else None,
                    "title": title,
                    "z_score": float(z),
                    "percent_change": float(pct_change),
                    "affected_count": cur_count,
                    "wards": [ward],
                    "suggested_dept": dept,
                    "sample_texts": samples,
                    "severity_score": severity_score,
                }
            )

    spikes.sort(key=lambda x: x["severity_score"], reverse=True)
    logger.info("Detected %d statistical spikes exceeding thresholds", len(spikes))
    return spikes


def rank_findings(spikes: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    """Select the top N most critical findings based on severity score.

    Args:
        spikes: List of spike finding dictionaries.
        top_n: Number of findings to return.

    Returns:
        Ranked sublist containing at most top_n findings.
    """
    return spikes[:top_n]
