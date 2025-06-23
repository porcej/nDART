from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import StatusReport
from extensions import db

from .utils import send_status_report_notification, handle_date_fields

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
