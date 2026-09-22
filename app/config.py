# Configuration settings for Grievance Radar.

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
BRIEFS_DIR = INSTANCE_DIR / "briefs"

os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(BRIEFS_DIR, exist_ok=True)


class BaseConfig:
    """Base configuration class with common settings."""

    SECRET_KEY = os.getenv("SECRET_KEY", "grievance-radar-default-secret-key-2026")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLUSTERING_ALGO = os.getenv("CLUSTERING_ALGO", "bertopic").lower()
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    ZSCORE_THRESHOLD = float(os.getenv("ZSCORE_THRESHOLD", "2.5"))
    PERCENT_CHANGE_THRESHOLD = float(os.getenv("PERCENT_CHANGE_THRESHOLD", "50.0"))
    ROLLING_WEEKS = int(os.getenv("ROLLING_WEEKS", "4"))
    MAX_FINDINGS = int(os.getenv("MAX_FINDINGS", "3"))
    INSTANCE_DIR = INSTANCE_DIR
    BRIEFS_DIR = BRIEFS_DIR


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'dev_radar.db'}"
    )


class TestingConfig(BaseConfig):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'prod_radar.db'}"
    )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
