FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_ENV=production

WORKDIR /app

# Install system dependencies (curl is required by the container HEALTHCHECK)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first so the (slow) layer can be cached
# independently of application code changes.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create volume mounts for persistent data
RUN mkdir -p instance/briefs instance/uploads

EXPOSE 5000

# /api/pipeline runs embeddings + clustering in-process, so give workers a
# generous timeout and allow them to finish in-flight requests on shutdown.
CMD ["gunicorn", \
     "-w", "2", \
     "-b", "0.0.0.0:5000", \
     "--timeout", "180", \
     "--graceful-timeout", "60", \
     "app:create_app()"]

# Used by Docker/Compose and by the CD smoke test to confirm the app is serving.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/health || exit 1
