# Database initialization and session management.

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize database with Flask application context.

    Imports the model module first so every table is registered on the
    SQLAlchemy metadata *before* ``create_all()`` runs. Without this, a process
    that imports only the ``app`` package (e.g. gunicorn loading
    ``app:create_app()``) creates an empty schema, because the models are
    otherwise imported later when the blueprints are registered.

    Args:
        app: Flask application instance.
    """
    from app import models  # noqa: F401 - imported for its model-registration side effect

    db.init_app(app)
    with app.app_context():
        db.create_all()
