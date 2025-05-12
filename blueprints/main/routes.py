from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort, current_app
from flask_login import login_required, current_user
from models import Event, Observation, Assignment, Agency, ObservationsCategory
from . import main_bp

@main_bp.route('/events')
@login_required
def events():
    assignments = Assignment.query.all()
    agencies = Agency.query.all()
    observations_categories = ObservationsCategory.query.all()
    return render_template('events.html', assignments=assignments, agencies=agencies, observations_categories=observations_categories, active_page='events', is_admin=current_user.is_admin)