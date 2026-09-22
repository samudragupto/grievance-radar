# REST API endpoint tests.

import io
import json
import pytest
from app.models import Complaint


def test_api_upload_csv(client, db):
    """Verify CSV file upload populates database and returns counts."""
    csv_content = (
        "text,ward,department,filed_date,category,is_synthetic\n"
        "Water supply missing since morning,Ward 4,Water Supply,2026-03-01,Water Supply,True\n"
        "Broken streetlight on main street,Ward 2,Streetlights,2026-03-02,Streetlights,True\n"
    )
    data = {
        "file": (io.BytesIO(csv_content.encode("utf-8")), "test_complaints.csv"),
    }
    res = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["imported"] == 2


def test_api_pipeline_triggers_and_returns(client, db, app):
    """Verify pipeline endpoint executes clustering and spike detection."""
    # Seed complaints first
    with app.app_context():
        from datetime import datetime
        for i in range(25):
            c = Complaint(
                text=f"Water leakage problem #{i} in sector",
                ward="Ward 4",
                department="Water Supply",
                filed_date=datetime(2026, 3, 10).date(),
            )
            db.session.add(c)
        db.session.commit()

    res = client.post("/api/pipeline")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "clusters_found" in data
    assert "top_findings" in data


def test_api_clusters_get(client):
    """Verify GET /api/clusters returns list."""
    res = client.get("/api/clusters")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_api_trends_aggregated_and_no_pii(client, app, db):
    """Verify /api/trends returns aggregated analytics with zero raw complaint texts."""
    with app.app_context():
        from datetime import datetime
        c = Complaint(
            text="Sensitive citizen personal info here that should not leak",
            ward="Ward 1",
            department="Sanitation",
            filed_date=datetime(2026, 3, 5).date(),
        )
        db.session.add(c)
        db.session.commit()

    res = client.get("/api/trends")
    assert res.status_code == 200
    data = res.get_json()

    # Verify no raw complaint text exists in JSON output
    serialized = json.dumps(data)
    assert "Sensitive citizen personal info" not in serialized
    assert "ward_counts" in data
    assert "ward_geo" in data
