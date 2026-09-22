# Database initialization and session management.

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize database with Flask application context.

    Args:
        app: Flask application instance.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
