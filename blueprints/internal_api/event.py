from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import Event
from extensions import db

from .utils import send_event_notification, handle_date_fields
from blueprints.race_context import (
    apply_race_filter,
    require_writable_race,
    require_writable_race_for_row,
)

event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

@event_bp.route('', methods=['POST'])
@event_bp.route('/', methods=['POST'])
@login_required
def api_create_event():
    """Create a new event"""
    try:
        race, err = require_writable_race()
        if err is not None:
            return err

        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format
        data.pop('race_id', None)

        cleaned_data = handle_date_fields(data)
        cleaned_data['race_id'] = race.id

        # Create a new event
        new_event = Event(**cleaned_data)
        db.session.add(new_event)
        db.session.commit()

        send_event_notification('new_event', new_event.to_dict())

        return jsonify({
            'data': [new_event.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500
    
@event_bp.route('', methods=['GET'])
@event_bp.route('/', methods=['GET'])
@event_bp.route('/<event_id>', methods=['GET'])
@login_required
def api_get_events(event_id=None):
    """
    Return Event data as a JSON in a format compatible with DataTables.
    Scoped to the current race.
    """
    if event_id is not None:
        events = apply_race_filter(
            Event.query.filter_by(id=event_id, delete_flag=False), Event
        ).all()
    else:
        events = apply_race_filter(
            Event.query.filter_by(delete_flag=False), Event
        ).all()

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
        data.pop('race_id', None)

        cleaned_data = handle_date_fields(data)

        event = apply_race_filter(Event.query.filter_by(id=event_id), Event).first()
        if event is None:
            return jsonify({'error': 'Event not found'}), 404

        _race, err = require_writable_race_for_row(event)
        if err is not None:
            return err
        
        # Update the event
        for key, value in cleaned_data.items():
            setattr(event, key, value)
        db.session.add(event)
        db.session.commit()

        send_event_notification('edit_event', event.to_dict())

        return jsonify({
            'data': [event.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500


@event_bp.route('/<event_id>', methods=['DELETE'])
@login_required
def api_delete_event(event_id):
    """soft Delete an existing event"""
    try:
        event = apply_race_filter(
            Event.query.filter_by(id=event_id, delete_flag=False), Event
        ).first()
        if event is None:
            return jsonify({'error': 'Event not found'}), 404

        _race, err = require_writable_race_for_row(event)
        if err is not None:
            return err
        
        event.delete_flag = True
        db.session.commit()

        send_event_notification('remove_event', event.to_dict())

        return jsonify({
            'data': [event.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500
