from flask import Blueprint
from .agency import agency_bp
from .event import event_bp
from .observation import observation_bp
from .assignment import assignment_bp
from .observation_category import observation_category_bp

internal_api_bp = Blueprint('internal_api_bp', __name__, url_prefix='/api')

internal_api_bp.register_blueprint(agency_bp)
internal_api_bp.register_blueprint(event_bp)
internal_api_bp.register_blueprint(observation_bp)
internal_api_bp.register_blueprint(assignment_bp)
internal_api_bp.register_blueprint(observation_category_bp)

__all__ = ['agency_bp', 'event_bp', 'observation_bp', 'assignment_bp', 'observation_category_bp']
