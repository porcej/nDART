from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Event
from extensions import db

from .utils import send_event_notification, handle_date_fields

event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

@event_bp.route('', methods=['POST'])
@event_bp.route('/', methods=['POST'])
@login_required
def api_create_event():
    """Create a new event"""
    try:
        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        # Create a new event
        new_event = Event(**cleaned_data)
        db.session.add(new_event)
        db.session.commit()

        send_event_notification('new_event', new_event.to_dict())

        return jsonify({
            'data': [new_event.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@event_bp.route('', methods=['GET'])
@event_bp.route('/', methods=['GET'])
@event_bp.route('/<event_id>', methods=['GET'])
@login_required
def api_get_events(event_id=None):
    """
    Return Event data as a JSON in a format compatible with DataTables.
    For a basic approact (client-side processing), we'll return all rows
    """
    if event_id is not None:
        events = Event.query.filter_by(id=event_id, delete_flag=False).all()
    else:
        events = Event.query.filter_by(delete_flag=False).all()

    data = [event.to_dict() for event in events]

    draw = request.args.get('draw', 1, type=int)
    recordsTotal = len(events)
    recordsFiltered = len(events)

    return jsonify({
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    })

@event_bp.route('/<event_id>', methods=['PUT'])
@login_required
def api_update_event(event_id):
    """Update an existing event"""
    try:
        data = request.get_json()['data'][event_id]  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        event = Event.query.filter_by(id=event_id).first()
        if event is None:
            return jsonify({'error': 'Event not found'}), 404
        
        # Update the event
        for key, value in cleaned_data.items():
            setattr(event, key, value)
        db.session.add(event)
        db.session.commit()

        send_event_notification('edit_event', event.to_dict())

        return jsonify({
            'data': [event.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@event_bp.route('/<event_id>', methods=['DELETE'])
@login_required
def api_delete_event(event_id):
    """soft Delete an existing event"""
    try:
        event = Event.query.filter_by(id=event_id, delete_flag=False).first()
        if event is None:
            return jsonify({'error': 'Event not found'}), 404
        
        event.delete_flag = True
        db.session.commit()

        send_event_notification('remove_event', event.to_dict())

        return jsonify({
            'data': [event.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
