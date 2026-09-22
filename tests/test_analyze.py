# Unit tests for baseline analysis and statistical spike detection.

from app.services.analyze import compute_rolling_baseline, detect_spikes, rank_findings


def test_rolling_baseline_computes_correct_mean_std():
    """Verify rolling baseline accurately aggregates historical weekly counts."""
    complaints = []
    # 4 weeks of 10 complaints per week for cluster 1 in Ward 4
    for w in range(1, 5):
        date_str = f"2026-01-{w*7:02d}"
        for _ in range(10):
            complaints.append(
                {
                    "cluster_id": 1,
                    "ward": "Ward 4",
                    "department": "Water Supply",
                    "filed_date": date_str,
                    "text": "Water leakage",
                }
            )

    baseline = compute_rolling_baseline(complaints, window_weeks=4)
    key = "1::Ward 4"
    assert key in baseline
    assert baseline[key]["mean"] > 0
    assert baseline[key]["std"] == 0.0  # Exact same counts every week yields zero std


def test_spike_detection_flags_injected_spike():
    """Verify statistical anomaly detection flags massive complaint surge."""
    complaints = []
    # Historical 4 weeks: 5 complaints per week
    for w in range(1, 5):
        date_str = f"2026-01-{w*7:02d}"
        for _ in range(5):
            complaints.append(
                {
                    "cluster_id": 1,
                    "ward": "Ward 4",
                    "department": "Water Supply",
                    "filed_date": date_str,
                    "text": "Normal water issue",
                }
            )

    # Current week: 45 complaints (+800% surge)
    current_date = "2026-02-15"
    for _ in range(45):
        complaints.append(
            {
                "cluster_id": 1,
                "ward": "Ward 4",
                "department": "Water Supply",
                "filed_date": current_date,
                "text": "Severe water crisis, no water reaching homes",
            }
        )

    baseline = compute_rolling_baseline(complaints, window_weeks=4)
    spikes = detect_spikes(complaints, baseline, z_thresh=2.0, pct_thresh=50.0)

    assert len(spikes) >= 1
    top_spike = spikes[0]
    assert top_spike["suggested_dept"] == "Water Supply"
    assert "Ward 4" in top_spike["wards"]
    assert top_spike["z_score"] >= 2.0


def test_spike_detection_does_not_flag_normal_variation():
    """Verify normal expected variations within 1 sigma are not flagged."""
    complaints = []
    # 5 weeks with roughly constant volume
    for w in range(1, 6):
        date_str = f"2026-01-{w*6:02d}"
        count = 10 if w < 5 else 11  # Only 1 extra complaint
        for _ in range(count):
            complaints.append(
                {
                    "cluster_id": 2,
                    "ward": "Ward 1",
                    "department": "Sanitation",
                    "filed_date": date_str,
                    "text": "Waste bin full",
                }
            )

    baseline = compute_rolling_baseline(complaints, window_weeks=4)
    spikes = detect_spikes(complaints, baseline, z_thresh=2.5, pct_thresh=50.0)
    assert len(spikes) == 0


def test_ranking_returns_findings_sorted_by_severity():
    """Verify rank_findings sorts in descending order of severity score."""
    spikes = [
        {"title": "Low", "severity_score": 10.0},
        {"title": "Critical", "severity_score": 95.0},
        {"title": "Medium", "severity_score": 45.0},
    ]
    ranked = rank_findings(spikes, top_n=2)
    assert len(ranked) == 2
    assert ranked[0]["title"] == "Critical"
    assert ranked[1]["title"] == "Medium"
