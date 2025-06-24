from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db
from models import User, Role, ChatRoom, Agency, StationStatus, Assignment, ObservationsCategory, Event, Observation, StatusReport
from datetime import datetime, UTC
from uuid import uuid4
from . import admin_bp
from .utils import admin_required
import pandas as pd
from io import BytesIO


# Dashboard
@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard."""
    # Get counts for dashboard cards
    users_count = User.query.count()
    roles_count = Role.query.count()
    assignments_count = Assignment.query.count()
    observations_categories_count = ObservationsCategory.query.count()
    station_statuses_count = StationStatus.query.count()
    active_statuses = StationStatus.query.filter_by(enabled=True).count()
    chat_rooms_count = ChatRoom.query.count()
    agencies_count = Agency.query.count()
    active_agencies = Agency.query.filter_by(enabled=True).count()
    events_count = Event.query.count()
    observations_count = Observation.query.count()
    status_reports_count = StatusReport.query.count()
    
    return render_template('admin/index.html',
                         username=current_user.name,
                         is_admin=True,
                         is_manager=current_user.is_manager,
                         users_count=users_count,
                         roles_count=roles_count,
                         assignments_count=assignments_count,
                         observations_categories_count=observations_categories_count,
                         station_statuses_count=station_statuses_count,
                         active_statuses=active_statuses,
                         chat_rooms_count=chat_rooms_count,
                         agencies_count=agencies_count,
                         active_agencies=active_agencies,
                         events_count=events_count,
                         observations_count=observations_count,
                         status_reports_count=status_reports_count)