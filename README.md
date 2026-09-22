# Grievance Radar

> One officer, one page, every week.

[![CI](https://github.com/samudragupto/grievance-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/samudragupto/grievance-radar/actions/workflows/ci.yml)
[![CD](https://github.com/samudragupto/grievance-radar/actions/workflows/cd.yml/badge.svg)](https://github.com/samudragupto/grievance-radar/actions/workflows/cd.yml)
[![CodeQL](https://github.com/samudragupto/grievance-radar/actions/workflows/codeql.yml/badge.svg)](https://github.com/samudragupto/grievance-radar/actions/workflows/codeql.yml)

Grievance Radar is an analytics platform for municipal administrators that turns high-volume citizen grievance feeds into actionable weekly decisions. The system ingests complaint data, redacts citizen PII, clusters complaints using dense semantic embeddings, flags statistical anomalies against rolling historical baselines, and generates an executive one-page "Monday Brief" PDF. A strict human-in-the-loop validation step requires municipal officers to confirm, dismiss, or refine automated findings before any anomaly enters the official brief.

## Screenshots

- `docs/screenshots/dashboard.png` (Officer review view)
- `docs/screenshots/trends.png` (Public trends & geospatial ward density)
- `docs/screenshots/monday_brief.png` (Compiled ReportLab one-page brief)

## How It Works

1. **Ingestion & Anonymization**: Citizen complaints (CSV/JSON) are normalized. Names, phone numbers, email addresses, and Aadhaar numbers are redacted at the gate.
2. **Dense Embeddings & Semantic Clustering**: Complaints are embedded using `sentence-transformers` (`all-MiniLM-L6-v2`) and clustered using BERTopic (with automatic fallback to K-Means and TF-IDF topic labeling).
3. **Rolling Baseline & Statistical Spike Detection**: Groups are tracked across rolling 4-week baselines. Surges exceeding $Z \ge 2.5\sigma$ and $+50\%$ over historical means are ranked by severity.
4. **Human-in-the-Loop Officer Verification**: An administrator confirms, dismisses, or edits the top findings. Only confirmed findings are compiled into the 1-page Monday Brief PDF.

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/grievance-radar.git
cd grievance-radar

# 2. Setup virtual environment & dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Seed database with synthetic sample data & run server
make seed
make run
```

Access the application at `http://localhost:5000`.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.x, Flask-SQLAlchemy |
| NLP & Vectors | sentence-transformers (`all-MiniLM-L6-v2`) |
| Clustering | BERTopic (primary), Scikit-Learn K-Means (fallback) |
| Statistical Engine | NumPy, SciPy (Z-score anomaly detection) |
| PDF Compilation | ReportLab (A4 1-page executive brief layout) |
| Database | SQLite |
| Frontend | Vanilla HTML5 / CSS3 / JavaScript (No heavy frameworks) |
| Data Visualizations | Chart.js 4.x, Leaflet.js (OpenStreetMap tiles) |
| Testing & CI | pytest, pytest-cov, GitHub Actions |

## Privacy & Synthetic Data Notice

Demo data in `data/` consists of 1,200 synthetic complaints modeled on CPGRAMS / DARPG formats. No genuine citizen PII is present or stored. The public trends view aggregates statistics by ward and category without exposing individual complaint texts.

## What's Included

- **Officer Review Dashboard**: Real-time review queue with inline text editing and single-click confirm/dismiss actions.
- **Public Trends View**: Privacy-preserving Chart.js time-series and Leaflet map showing municipal ward density.
- **Monday Brief Generator**: ReportLab engine generating an executive one-page briefing document for municipal commissioners.
- **Full CLI Pipeline**: `scripts/run_pipeline.py` for headless ingestion and automated reporting in cron workflows.

## Development & Testing

```bash
# Install dev tooling (pytest, coverage, linting)
make install-dev

# Run pytest test suite with coverage
make test

# Code formatting and linting (identical to what CI enforces)
make format
make lint

# Boot the app and verify the key routes respond
make smoke

# Optional: auto-run the linters on every commit
pip install pre-commit && pre-commit install
```

## CI/CD

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | PRs into `main`, manual (`workflow_dispatch`), reusable (`workflow_call`) | Lint (`black`, `isort`, `flake8`) + pytest with coverage + in-process smoke test of the WSGI app |
| `cd.yml` | Pushes to `main` | Runs CI as a gate, builds the container image, smoke-tests it over HTTP (`/health`), then fires the Render deploy hook |
| `codeql.yml` | Pushes/PRs to `main`, weekly schedule | CodeQL static analysis for Python |

Notes:

- The lint job installs only [`requirements-lint.txt`](requirements-lint.txt), so it finishes in seconds instead of pulling the full ML stack.
- The `sentence-transformers` model is cached in `~/.cache/huggingface`; the cache key includes `hashFiles('requirements*.txt')` so a dependency bump invalidates it.
- `GET /health` is the liveness probe used by the container `HEALTHCHECK`, the compose healthcheck, and the CD smoke test.
- If `RENDER_DEPLOY_HOOK` is not configured, CD logs a warning and skips the deploy instead of reporting a misleading green run.
- To deploy, add these repository secrets under **Settings -> Secrets and variables -> Actions**: `RENDER_DEPLOY_HOOK` (Render), or `PYTHONANYWHERE_USERNAME` / `PYTHONANYWHERE_API_TOKEN` / `PYTHONANYWHERE_DOMAIN` and enable the `deploy_pythonanywhere` job.

Docker:

```bash
make docker-build          # build grievance-radar:local
SECRET_KEY=... make docker-up   # start the stack (SECRET_KEY is required)
```

## Credits & Hackathon

Built for **YUVA Megathon 2026** at **SRM Institute of Science & Technology, Tiruchirappalli**.

## License

MIT License. See [LICENSE](LICENSE) for details.
