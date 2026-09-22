# Flask application factory for Grievance Radar.

import logging
import os

from flask import Flask

from app.config import config_by_name
from app.database import init_db


def create_app(config_name: str = None) -> Flask:
    """Create and configure an instance of the Flask application.

    Args:
        config_name: Target environment name ('development', 'testing', 'production').

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    app = Flask(__name__, instance_relative_config=True)

    # Configure Logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] in %(module)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Load configuration
    selected_config = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(selected_config)
    logger.info("Initializing Grievance Radar with %s config", config_name)

    # Initialize Database
    init_db(app)

    # Register Blueprints
    from app.routes.api import api_bp
    from app.routes.brief import brief_bp
    from app.routes.main import main_bp
    from app.routes.officer import officer_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(brief_bp)

    return app
