from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import StafferAROVolunteer, Assignment, AppSettings
import requests

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
        
        # Get API configuration
        api_url = AppSettings.get_setting('staffer_api_url', 'http://localhost:8091/public-api/v1')
        api_key = AppSettings.get_setting('staffer_api_key', '')
        
        if not api_key:
            return jsonify({'error': 'Staffer API key not configured'}), 400
        
        # Prepare the check-in request
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'Accept': 'application/json'
        }
        
        payload = {
            'callsign': callsign,
            'status': status
        }
        
        # Send check-in to staffer API
        response = requests.post(
            f"{api_url.rstrip('/')}/checkin",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201, 204]:
            return jsonify({
                'success': f'Updated status for {callsign} in staffer database'
            })
        else:
            error_msg = f'Staffer API returned status {response.status_code}'
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
                elif 'detail' in error_data:
                    error_msg = error_data['detail']
            except:
                pass
            
            return jsonify({
                'error': error_msg,
                'warning': f'Status report saved but staffer update failed for {callsign}'
            }), 400
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'Connection error: {str(e)}',
            'warning': 'Status report saved but could not connect to staffer API'
        }), 500
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'warning': 'Status report saved but staffer update failed'
        }), 500
