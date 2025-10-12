from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import StatusReport, Assignment, StationStatus, AppSettings
from extensions import db

from .utils import send_status_report_notification, handle_date_fields
from .staffer_api_service import send_status_report_to_staffer, update_status_report_in_staffer

status_report_bp = Blueprint('status_report_bp', __name__, url_prefix='/status_reports')

@status_report_bp.route('', methods=['POST'])
@status_report_bp.route('/', methods=['POST'])
@login_required
def api_create_status_report():
    """Create a new status report"""
    try:
        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        # Create a new status report
        new_status_report = StatusReport(**cleaned_data)
        db.session.add(new_status_report)
        db.session.commit()

        send_status_report_notification('new_status_report', new_status_report.to_dict())

        # Send to staffer API if configured
        staffer_enabled = AppSettings.get_setting('staffer_api_enabled', 'false')
        if staffer_enabled.lower() == 'true':
            try:
                # Get additional data for the API call
                reporter_data = None
                status_data = None
                
                if new_status_report.reporter_id:
                    reporter = Assignment.query.get(new_status_report.reporter_id)
                    if reporter:
                        reporter_data = {
                            'id': reporter.id,
                            'name': reporter.name if hasattr(reporter, 'name') else None,
                        }
                
                if new_status_report.status_id:
                    status = StationStatus.query.get(new_status_report.status_id)
                    if status:
                        status_data = {
                            'id': status.id,
                            'name': status.name if hasattr(status, 'name') else None,
                        }
                
                # Prepare status report data
                status_report_data = {
                    'time': new_status_report.time,
                    'reporter_id': new_status_report.reporter_id,
                    'status_id': new_status_report.status_id,
                    'comment': new_status_report.comment
                }
                
                result = send_status_report_to_staffer(status_report_data, reporter_data, status_data)
                
                # Log the result but don't fail the main operation
                if not result.get('success'):
                    print(f"Warning: Failed to send status report to staffer API: {result.get('error')}")
                    
            except Exception as staffer_error:
                # Log the error but don't fail the main operation
                print(f"Warning: Exception while sending to staffer API: {str(staffer_error)}")

        return jsonify({
            'data': [new_status_report.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@status_report_bp.route('', methods=['GET'])
@status_report_bp.route('/', methods=['GET'])
@status_report_bp.route('/<status_report_id>', methods=['GET'])
@login_required
def api_get_status_reports(status_report_id=None):
    """
    Return StatusReport data as a JSON in a format compatible with DataTables.
    For a basic approact (client-side processing), we'll return all rows
    """
    if status_report_id is not None:
        status_reports = StatusReport.query.filter_by(id=status_report_id, delete_flag=False).all()
    else:
        status_reports = StatusReport.query.filter_by(delete_flag=False).all()

    data = [status_report.to_dict() for status_report in status_reports]

    draw = request.args.get('draw', 1, type=int)
    recordsTotal = len(status_reports)
    recordsFiltered = len(status_reports)

    return jsonify({
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    })

@status_report_bp.route('/<status_report_id>', methods=['PUT'])
@login_required
def api_update_status_report(status_report_id):
    """Update an existing status report"""
    try:
        data = request.get_json()['data'][status_report_id]  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        status_report = StatusReport.query.filter_by(id=status_report_id).first()
        if status_report is None:
            return jsonify({'error': 'Status report not found'}), 404
        
        # Update the status report
        for key, value in cleaned_data.items():
            setattr(status_report, key, value)
        db.session.add(status_report)
        db.session.commit()

        send_status_report_notification('edit_status_report', status_report.to_dict())

        # Update in staffer API if configured
        staffer_enabled = AppSettings.get_setting('staffer_api_enabled', 'false')
        if staffer_enabled.lower() == 'true':
            try:
                # Get additional data for the API call
                reporter_data = None
                status_data = None
                
                if status_report.reporter_id:
                    reporter = Assignment.query.get(status_report.reporter_id)
                    if reporter:
                        reporter_data = {
                            'id': reporter.id,
                            'name': reporter.name if hasattr(reporter, 'name') else None,
                        }
                
                if status_report.status_id:
                    status = StationStatus.query.get(status_report.status_id)
                    if status:
                        status_data = {
                            'id': status.id,
                            'name': status.name if hasattr(status, 'name') else None,
                        }
                
                # Prepare status report data
                status_report_data = {
                    'time': status_report.time,
                    'reporter_id': status_report.reporter_id,
                    'status_id': status_report.status_id,
                    'comment': status_report.comment
                }
                
                result = update_status_report_in_staffer(status_report_id, status_report_data, reporter_data, status_data)
                
                # Log the result but don't fail the main operation
                if not result.get('success'):
                    print(f"Warning: Failed to update status report in staffer API: {result.get('error')}")
                    
            except Exception as staffer_error:
                # Log the error but don't fail the main operation
                print(f"Warning: Exception while updating in staffer API: {str(staffer_error)}")

        return jsonify({
            'data': [status_report.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@status_report_bp.route('/<status_report_id>', methods=['DELETE'])
@login_required
def api_delete_status_report(status_report_id):
    """soft Delete an existing status report"""
    try:
        status_report = StatusReport.query.filter_by(id=status_report_id, delete_flag=False).first()
        if status_report is None:
            return jsonify({'error': 'Status report not found'}), 404
        
        status_report.delete_flag = True
        db.session.commit()

        send_status_report_notification('remove_status_report', status_report.to_dict())

        return jsonify({
            'data': [status_report.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
