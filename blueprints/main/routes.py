from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort, current_app
from flask_login import login_required, current_user
from models import Event, Observation, Assignment, Agency, ObservationsCategory, StationStatus
from . import main_bp

def get_form_options():
    """Get the form options for the dashboard"""
    return {
        'assignments': [assignment.to_form_options() for assignment in Assignment.query.filter_by(enabled=True).order_by(Assignment.sort_order).all()],
        'agencies': [agency.to_form_options() for agency in Agency.query.filter_by(enabled=True).order_by(Agency.sort_order).all()],
        'observations_categories': [category.to_form_options() for category in ObservationsCategory.query.filter_by(enabled=True).order_by(ObservationsCategory.sort_order).all()],
        'station_statuses': [station_status.to_form_options() for station_status in StationStatus.query.filter_by(enabled=True).order_by(StationStatus.sort_order).all()]
    }

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', form_options=get_form_options())

@main_bp.route('/events')
@login_required
def events():
    return render_template('events.html', form_options=get_form_options())

@main_bp.route('/observations')
@login_required
def observations():
    return render_template('observations.html', form_options=get_form_options())

@main_bp.route('/status_reports')
@login_required
def status_reports():
    return render_template("status_reports.html", form_options=get_form_options())
