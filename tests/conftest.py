# Test configuration and fixtures.

from datetime import datetime
import json
from pathlib import Path
import pytest
from app import create_app
from app.database import db as _db
from app.models import Complaint


@pytest.fixture(scope="session")
def app():
    """Create Flask application fixture configured for testing."""
    test_app = create_app("testing")
    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Provide a test client for simulating HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Provide database session rollback after each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def sample_complaints():
    """Load sample complaints from synthetic dataset file."""
    data_path = Path(__file__).resolve().parent.parent / "data" / "sample_complaints.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)[:100]
    return [
        {
            "id": 1,
            "text": "Water pipeline burst in Ward 4 causing flooding.",
            "ward": "Ward 4",
            "department": "Water Supply",
            "filed_date": "2026-03-10",
        }
    ]
