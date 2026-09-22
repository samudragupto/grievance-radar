.PHONY: run test lint format seed pipeline clean help

help:
	@echo "Available commands:"
	@echo "  make run       - Run Flask development server"
	@echo "  make test      - Run pytest test suite with coverage"
	@echo "  make lint      - Check code style with black, isort, and flake8"
	@echo "  make format    - Autoformat code with black and isort"
	@echo "  make seed      - Ingest sample complaints and seed database"
	@echo "  make pipeline  - Run full ML pipeline via CLI"
	@echo "  make clean     - Clean cache files and compiled artifacts"

run:
	FLASK_APP=app:create_app FLASK_ENV=development flask run --debug --port 5000

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	black --check .
	isort --check .
	flake8 app/ tests/ scripts/

format:
	black .
	isort .
	flake8 app/ tests/ scripts/

seed:
	python scripts/seed_db.py

pipeline:
	python scripts/run_pipeline.py --input data/sample_complaints.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/ *.egg-info
