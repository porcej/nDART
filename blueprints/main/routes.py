from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Assignment, Agency, ObservationsCategory, StationStatus, StafferAROVolunteer
from blueprints.race_context import set_current_race, apply_race_filter
from . import main_bp

def get_form_options():
    """Get the form options for the dashboard"""
    return {
        'assignments': [assignment.to_form_options() for assignment in Assignment.query.filter_by(enabled=True).order_by(Assignment.sort_order).all()],
        'agencies': [agency.to_form_options() for agency in Agency.query.filter_by(enabled=True).order_by(Agency.sort_order).all()],
        'observations_categories': [category.to_form_options() for category in ObservationsCategory.query.filter_by(enabled=True).order_by(ObservationsCategory.sort_order).all()],
        'station_statuses': [station_status.to_form_options() for station_status in StationStatus.query.filter_by(enabled=True).order_by(StationStatus.sort_order).all()]
    }

@main_bp.route('/select-race', methods=['POST'])
@login_required
def select_race():
    """Set the current race in the session and redirect back."""
    race_id = request.form.get('race_id') or request.args.get('race_id')
    race = set_current_race(race_id) if race_id else None
    if race is None:
        flash('Race not found.', 'error')
    next_url = request.form.get('next') or request.referrer or url_for('main_bp.dashboard')
    return redirect(next_url)

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

@main_bp.route('/aro-roster')
@login_required
def aro_roster():
    """Display ARO volunteers roster (public view)."""
    return render_template('aro_roster.html')

@main_bp.route('/aro-roster/data', methods=['GET'])
@login_required
def get_aro_roster_data():
    """Get ARO volunteers data as JSON for DataTables."""
    try:
        volunteers = apply_race_filter(StafferAROVolunteer.query, StafferAROVolunteer).all()
        
        data = []
        for volunteer in volunteers:
            data.append({
                'id': volunteer.id,
                'assignment_name': volunteer.assignment.name if volunteer.assignment else '',
                'assignment_id': volunteer.assignment_id,
                'staffer_assignment': volunteer.staffer_assignment or '',
                'short_code': volunteer.short_code or '',
                'callsign': volunteer.callsign,
                'name': volunteer.name or '',
                'email': volunteer.email or '',
                'phone_number': volunteer.phone_number or '',
                'status': volunteer.status or '',
                'status_timestamp': volunteer.status_timestamp.strftime('%Y-%m-%d %H:%M') if volunteer.status_timestamp else ''
            })
        
        return jsonify({
            'data': data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
