from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db
from models import User, Role, ChatRoom, Agency, StationStatus, Assignment, ObservationsCategory, Event, Observation, StatusReport, AppSettings, Race
from datetime import datetime, UTC
from uuid import uuid4
from . import admin_bp
from .utils import admin_required
from blueprints.race_context import apply_race_filter
import pandas as pd
from io import BytesIO


def remove_all_rows(table_name):
    """Helper function to remove all rows from a table for the current race."""
    if table_name == 'events':
        apply_race_filter(Event.query, Event).delete(synchronize_session=False)
    elif table_name == 'observations':
        apply_race_filter(Observation.query, Observation).delete(synchronize_session=False)
    db.session.commit()


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
    chat_rooms_count = apply_race_filter(ChatRoom.query, ChatRoom).count()
    agencies_count = Agency.query.count()
    active_agencies = Agency.query.filter_by(enabled=True).count()
    events_count = apply_race_filter(Event.query, Event).count()
    observations_count = apply_race_filter(Observation.query, Observation).count()
    status_reports_count = apply_race_filter(StatusReport.query, StatusReport).count()
    races_count = Race.query.count()
    
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
                         status_reports_count=status_reports_count,
                         races_count=races_count,
                         active_users=User.query.filter_by(active=True).count())


# Legacy admin route (moved from app.py)
@admin_bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    """Legacy admin route for uploading xlsx file and removing all rows."""
    if not current_user.is_admin:
        return redirect(url_for('main_bp.dashboard'))
    if request.method == 'POST':
        if 'remove-events' in request.form:
            remove_all_rows('events')
            return f'All events removed.'
        elif 'remove-observations' in request.form:
            remove_all_rows('observations')
            return f'All observations removed.'
        else:
            return 'I am not a teapot.'

    return render_template('admin.html', active_page='admin', is_admin=current_user.is_admin)