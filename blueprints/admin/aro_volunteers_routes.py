from flask import render_template, jsonify
from flask_login import login_required, current_user
from models import StafferAROVolunteer
from . import admin_bp
from .utils import admin_required
from blueprints.race_context import apply_race_filter


@admin_bp.route('/aro-volunteers')
@login_required
@admin_required
def aro_volunteers():
    """Display ARO volunteers from staffer database for the current race."""
    volunteers = apply_race_filter(StafferAROVolunteer.query, StafferAROVolunteer).all()
    
    volunteers_data = []
    for volunteer in volunteers:
        volunteers_data.append({
            'id': volunteer.id,
            'assignment_name': volunteer.assignment.name if volunteer.assignment else None,
            'assignment_id': volunteer.assignment_id,
            'staffer_assignment_name': volunteer.staffer_assignment,
            'staffer_assignment_code': volunteer.short_code,
            'callsign': volunteer.callsign,
            'name': volunteer.name,
            'email': volunteer.email,
            'phone_number': volunteer.phone_number
        })
    
    return render_template('admin/aro_volunteers.html',
                         volunteers=volunteers_data,
                         username=current_user.name,
                         is_admin=True,
                         is_manager=current_user.is_manager)


@admin_bp.route('/aro-volunteers/data', methods=['GET'])
@login_required
@admin_required
def get_aro_volunteers_data():
    """Get ARO volunteers data as JSON for DataTables."""
    try:
        volunteers = apply_race_filter(StafferAROVolunteer.query, StafferAROVolunteer).all()
        
        data = []
        for volunteer in volunteers:
            data.append({
                'id': volunteer.id,
                'assignment_name': volunteer.assignment.name if volunteer.assignment else '',
                'assignment_id': volunteer.assignment_id,
                'staffer_assignment_name': volunteer.staffer_assignment or '',
                'staffer_assignment_code': volunteer.short_code or '',
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
