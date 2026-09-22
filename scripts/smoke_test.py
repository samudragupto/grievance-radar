# Post-deploy / post-build smoke test.
#
# Boots the Flask app, ensures the schema exists, and asserts that the routes a
# monitoring probe depends on respond with HTTP 200. Used by the CI pipeline
# and by the CD container smoke test so a broken image never gets deployed.
#
# Usage: python scripts/smoke_test.py [base_url]
#   - With no argument: exercises the in-process Flask test client.
#   - With a base URL: exercises a live server (e.g. http://127.0.0.1:5000).

import sys
from pathlib import Path

# Allow `python scripts/smoke_test.py` from anywhere: running a script that
# lives in scripts/ puts that directory (not the repo root) on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EXPECTED_ROUTES = ["/health", "/", "/trends", "/clusters", "/officer/dashboard"]


def check_in_process() -> int:
    """Run the smoke checks against the in-process test client.

    Deliberately does NOT call `db.create_all()` itself: the app factory must
    create the schema on boot (that is all a gunicorn worker does), so calling
    it here would hide bootstrap regressions from the pipeline.
    """
    from app import create_app

    app = create_app("testing")
    client = app.test_client()
    failures = []
    for route in EXPECTED_ROUTES:
        response = client.get(route)
        status = response.status_code
        print(f"[in-process] GET {route} -> {status}")
        if status != 200:
            failures.append(route)

    health = client.get("/health").get_json()
    if not health or health.get("status") != "ok":
        print(f"[in-process] unexpected /health payload: {health}")
        failures.append("/health payload")

    return 1 if failures else 0


def check_live(base_url: str) -> int:
    """Run the smoke checks against an already-running server."""
    import urllib.error
    import urllib.request

    failures = []
    for route in EXPECTED_ROUTES:
        url = f"{base_url.rstrip('/')}{route}"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller
            print(f"[live] GET {url} -> ERROR {exc}")
            failures.append(route)
            continue

        print(f"[live] GET {url} -> {status}")
        if status != 200:
            failures.append(route)

    return 1 if failures else 0


def main(argv):
    base_url = argv[1] if len(argv) > 1 else None
    if base_url:
        return check_live(base_url)
    return check_in_process()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
