from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import StationStatus
from extensions import db

from .utils import send_update_notification, handle_date_fields

station_status_bp = Blueprint('station_status_bp', __name__, url_prefix='/station_statuses')

@station_status_bp.route('', methods=['POST'])
@station_status_bp.route('/', methods=['POST'])
@login_required
def api_create_station_status():
    """Create a new station status"""
    try:
        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        # Create a new station status
        new_station_status = StationStatus(**cleaned_data)
        db.session.add(new_station_status)
        db.session.commit()

        send_update_notification('station_status_update')

        return jsonify({
            'data': [new_station_status.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500
    
@station_status_bp.route('', methods=['GET'])
@station_status_bp.route('/', methods=['GET'])
@station_status_bp.route('/<station_status_id>', methods=['GET'])
@login_required
def api_get_station_statuses(station_status_id=None):
    """
    Return StationStatus data as a JSON in a format compatible with DataTables.
    For a basic approact (client-side processing), we'll return all rows
    """
    # if station_status_id is not None:
    #     station_statuses = StationStatus.query.filter_by(id=station_status_id, delete_flag=False).all()
    # else:
    #     station_statuses = StationStatus.query.filter_by(delete_flag=False).all()

    if station_status_id is not None:
        station_statuses = StationStatus.query.filter_by(id=station_status_id).all()
    else:
        station_statuses = StationStatus.query.all()

    data = [station_status.to_dict() for station_status in station_statuses]

    draw = request.args.get('draw', 1, type=int)
    recordsTotal = len(station_statuses)
    recordsFiltered = len(station_statuses)

    return jsonify({
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    })

@station_status_bp.route('/<station_status_id>', methods=['PUT'])
@login_required
def api_update_station_status(station_status_id):
    """Update an existing station status"""
    try:
        data = request.get_json()['data'][station_status_id]  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        station_status = StationStatus.query.filter_by(id=station_status_id).first()
        if station_status is None:
            return jsonify({'error': 'Station status not found'}), 404
        
        # Update the station status
        for key, value in cleaned_data.items():
            setattr(station_status, key, value)
        db.session.add(station_status)
        db.session.commit()

        send_update_notification('station_status_update')

        return jsonify({
            'data': [station_status.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500


@station_status_bp.route('/<station_status_id>', methods=['DELETE'])
@login_required
def api_delete_station_status(station_status_id):
    """soft Delete an existing station status"""
    try:
        station_status = StationStatus.query.filter_by(id=station_status_id, delete_flag=False).first()
        if station_status is None:
            return jsonify({'error': 'Station status not found'}), 404
        
        station_status.delete_flag = True
        db.session.commit()

        send_update_notification('station_status_update')

        return jsonify({
            'data': [station_status.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500
