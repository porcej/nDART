from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import StatusReport
from extensions import db

from .utils import send_status_report_notification, handle_date_fields
from blueprints.race_context import (
    apply_race_filter,
    require_writable_race,
    require_writable_race_for_row,
)

status_report_bp = Blueprint('status_report_bp', __name__, url_prefix='/status_reports')

@status_report_bp.route('', methods=['POST'])
@status_report_bp.route('/', methods=['POST'])
@login_required
def api_create_status_report():
    """Create a new status report"""
    try:
        race, err = require_writable_race()
        if err is not None:
            return err

        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format
        data.pop('race_id', None)

        cleaned_data = handle_date_fields(data)
        cleaned_data['race_id'] = race.id

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
    Scoped to the current race.
    """
    if status_report_id is not None:
        status_reports = apply_race_filter(
            StatusReport.query.filter_by(id=status_report_id, delete_flag=False), StatusReport
        ).all()
    else:
        status_reports = apply_race_filter(
            StatusReport.query.filter_by(delete_flag=False), StatusReport
        ).all()

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
        data = request.get_json()['data'][status_report_id]
        data.pop('race_id', None)

        cleaned_data = handle_date_fields(data)

        status_report = apply_race_filter(
            StatusReport.query.filter_by(id=status_report_id), StatusReport
        ).first()
        if status_report is None:
            return jsonify({'error': 'Status report not found'}), 404

        _race, err = require_writable_race_for_row(status_report)
        if err is not None:
            return err
        
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
    """soft Delete one or more status reports"""
    try:
        request_data = request.get_json() if request.data else None
        
        deleted_reports = []
        
        if request_data and 'data' in request_data:
            ids_to_delete = list(request_data['data'].keys())
            
            for report_id in ids_to_delete:
                status_report = apply_race_filter(
                    StatusReport.query.filter_by(id=report_id, delete_flag=False), StatusReport
                ).first()
                if status_report:
                    _race, err = require_writable_race_for_row(status_report)
                    if err is not None:
                        return err
                    status_report.delete_flag = True
                    deleted_reports.append(status_report.to_dict())
                    send_status_report_notification('remove_status_report', status_report.to_dict())
            
            if not deleted_reports:
                return jsonify({'error': 'No status reports found'}), 404
            
            db.session.commit()
            
            return jsonify({
                'data': deleted_reports
            })
        else:
            status_report = apply_race_filter(
                StatusReport.query.filter_by(id=status_report_id, delete_flag=False), StatusReport
            ).first()
            if status_report is None:
                return jsonify({'error': 'Status report not found'}), 404

            _race, err = require_writable_race_for_row(status_report)
            if err is not None:
                return err
            
            status_report.delete_flag = True
            db.session.commit()

            send_status_report_notification('remove_status_report', status_report.to_dict())

            return jsonify({
                'data': [status_report.to_dict()]
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
