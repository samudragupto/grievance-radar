# Tests for the application factory and database bootstrap.

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Boots the app exactly the way gunicorn does (`app:create_app()`): only the
# `app` package is imported, so nothing else registers the models first.
BOOTSTRAP_PROBE = (
    "from app import create_app\n"
    "app = create_app('production')\n"
    "client = app.test_client()\n"
    "response = client.get('/health')\n"
    "assert response.status_code == 200, response.get_data(as_text=True)\n"
    "print('bootstrap ok')\n"
)


def test_fresh_process_boots_with_a_created_schema(tmp_path):
    """A process importing only the `app` package must still get a real schema.

    Regression test: `create_all()` previously ran before the model modules were
    imported (they are pulled in later, when blueprints register), so a gunicorn
    worker loading `app:create_app()` created an empty database and every
    database-backed route answered 500. Tests never saw it because conftest
    imports `app.models` and the old smoke script called `create_all()` itself.
    """
    db_path = tmp_path / "prod_radar.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "PYTHONPATH": str(REPO_ROOT),
    }

    result = subprocess.run(
        [sys.executable, "-c", BOOTSTRAP_PROBE],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert db_path.exists(), "application did not create its database file"


def test_health_endpoint_reports_unhealthy_when_db_is_broken(app):
    """The deploy probe must surface a broken database as a 503, not a 200."""
    from app.database import db

    client = app.test_client()
    healthy = client.get("/health")
    assert healthy.status_code == 200
    assert healthy.get_json()["status"] == "ok"

    with app.app_context():
        db.drop_all()

    broken = client.get("/health")
    assert broken.status_code == 503
    assert broken.get_json()["status"] == "unhealthy"
