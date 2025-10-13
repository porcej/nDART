from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import StafferAROVolunteer, Assignment, AppSettings
from .staffer_api_service import checkin_volunteer_to_staffer

staffer_volunteers_bp = Blueprint('staffer_volunteers_bp', __name__, url_prefix='/staffer-volunteers')

@staffer_volunteers_bp.route('/by-assignment/<assignment_id>', methods=['GET'])
@login_required
def api_get_volunteers_by_assignment(assignment_id):
    """
    Get all volunteers assigned to a specific assignment
    """
    try:
        volunteers = StafferAROVolunteer.query.filter_by(assignment_id=assignment_id).all()
        
        return jsonify({
            'success': True,
            'data': [v.to_dict() for v in volunteers],
            'count': len(volunteers)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@staffer_volunteers_bp.route('', methods=['GET'])
@staffer_volunteers_bp.route('/', methods=['GET'])
@login_required
def api_get_all_volunteers():
    """
    Get all volunteers with their assignment info
    """
    try:
        volunteers = StafferAROVolunteer.query.all()
        
        data = []
        for v in volunteers:
            volunteer_dict = v.to_dict()
            if v.assignment:
                volunteer_dict['assignment_name'] = v.assignment.name
            data.append(volunteer_dict)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(volunteers)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@staffer_volunteers_bp.route('/checkin', methods=['POST'])
@login_required
def api_checkin_volunteer():
    """
    Check in a volunteer to the staffer database by updating their status
    """
    try:
        data = request.get_json()
        callsign = data.get('callsign')
        status = data.get('status')
        
        if not callsign or not status:
            return jsonify({'error': 'Callsign and status are required'}), 400
        
        # Check if staffer API is enabled
        staffer_enabled = AppSettings.get_setting('staffer_api_enabled', 'false')
        if staffer_enabled.lower() != 'true':
            return jsonify({'success': 'Staffer API integration is disabled'}), 200
        
        # Use the centralized service function
        result = checkin_volunteer_to_staffer(callsign, status)
        
        if result['success']:
            return jsonify({
                'success': result['message']
            })
        else:
            return jsonify({
                'error': result['error'],
                'warning': f'Status report saved but staffer update failed for {callsign}'
            }), 400
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'warning': 'Status report saved but staffer update failed'
        }), 500
