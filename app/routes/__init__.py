# Blueprint registration for Grievance Radar routes.

from app.routes.api import api_bp
from app.routes.brief import brief_bp
from app.routes.main import main_bp
from app.routes.officer import officer_bp

__all__ = ["main_bp", "officer_bp", "api_bp", "brief_bp"]
