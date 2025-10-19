from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# from . import routes, users_routes, roles_routes, chat_room_routes, station_statuses, observations_categories
from . import assignments_routes, users_routes, routes, roles_routes, chat_room_routes, station_statuses, observations_categories, agencies_routes, settings_routes, staffer_mappings_routes, aro_volunteers_routes, events_routes, observations_routes