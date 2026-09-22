.PHONY: run test lint format seed pipeline smoke install install-dev docker-build docker-up clean help

help:
	@echo "Available commands:"
	@echo "  make install     - Install runtime dependencies"
	@echo "  make install-dev - Install runtime + dev/test/lint dependencies"
	@echo "  make run         - Run Flask development server"
	@echo "  make test        - Run pytest test suite with coverage"
	@echo "  make lint        - Check code style with black, isort, and flake8 (same as CI)"
	@echo "  make format      - Autoformat code with black and isort"
	@echo "  make smoke       - Boot the app and verify key routes respond"
	@echo "  make seed        - Ingest sample complaints and seed database"
	@echo "  make pipeline    - Run full ML pipeline via CLI"
	@echo "  make docker-build- Build the production container image"
	@echo "  make docker-up   - Start the stack with docker compose"
	@echo "  make clean       - Clean cache files and compiled artifacts"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt

run:
	FLASK_APP=app:create_app FLASK_ENV=development flask run --debug --port 5000

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	black --check .
	isort --check-only .
	flake8 app/ tests/ scripts/

format:
	black .
	isort .
	flake8 app/ tests/ scripts/

smoke:
	python scripts/smoke_test.py

# `-m scripts.<name>` (not `python scripts/<name>.py`) so the repository root is
# on sys.path and the `app` / `scripts` packages resolve correctly.
seed:
	python -m scripts.seed_db

pipeline:
	python -m scripts.run_pipeline --input data/sample_complaints.json

docker-build:
	docker build -t grievance-radar:local .

docker-up:
	docker compose up --build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/ *.egg-info
