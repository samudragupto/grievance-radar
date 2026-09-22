# Route and view tests for web interface.

import json
import pytest
from app.models import Finding


def test_get_index(client):
    """Verify home landing page returns HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Grievance Radar" in response.data


def test_get_officer_dashboard(client):
    """Verify officer dashboard page renders successfully."""
    response = client.get("/officer/dashboard")
    assert response.status_code == 200
    assert b"Officer Review Dashboard" in response.data


def test_get_trends_page(client):
    """Verify public trends page renders successfully."""
    response = client.get("/trends")
    assert response.status_code == 200
    assert b"Public Anonymized Trends" in response.data


def test_post_officer_decision_valid(client, app, db):
    """Verify officer decision confirmation updates finding and returns success."""
    with app.app_context():
        finding = Finding(
            title="Transformer Sparking in Ward 3",
            z_score=3.2,
            percent_change=120.0,
            affected_count=25,
            wards=json.dumps(["Ward 3"]),
            suggested_dept="Electrical",
            sample_texts=json.dumps(["Dangerous sparking"]),
            status="pending",
        )
        db.session.add(finding)
        db.session.commit()
        finding_id = finding.id

    response = client.post(
        "/officer/decision",
        json={"finding_id": finding_id, "action": "confirm"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["finding"]["status"] == "confirmed"


def test_post_officer_decision_invalid_id(client):
    """Verify invalid finding_id returns HTTP 404."""
    response = client.post(
        "/officer/decision",
        json={"finding_id": 999999, "action": "confirm"},
    )
    assert response.status_code == 404
