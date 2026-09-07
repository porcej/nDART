from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import Observation
from extensions import db

from .utils import send_observation_notification, handle_date_fields
from blueprints.race_context import (
    apply_race_filter,
    require_writable_race,
    require_writable_race_for_row,
)

observation_bp = Blueprint('observation_bp', __name__, url_prefix='/observations')

@observation_bp.route('', methods=['POST'])
@observation_bp.route('/', methods=['POST'])
@login_required
def api_create_observation():
    """Create a new observation"""
    try:
        race, err = require_writable_race()
        if err is not None:
            return err

        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format
        data.pop('race_id', None)

        cleaned_data = handle_date_fields(data)
        cleaned_data['race_id'] = race.id

        # Create a new observation
        new_observation = Observation(**cleaned_data)
        db.session.add(new_observation)
        db.session.commit()

        send_observation_notification('new_observation', new_observation.to_dict())

        return jsonify({
            'data': [new_observation.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500
    
@observation_bp.route('', methods=['GET'])
@observation_bp.route('/', methods=['GET'])
@observation_bp.route('/<observation_id>', methods=['GET'])
@login_required
def api_get_observations(observation_id=None):
    """
    Return Observation data as a JSON in a format compatible with DataTables.
    Scoped to the current race.
    """
    if observation_id is not None:
        observations = apply_race_filter(
            Observation.query.filter_by(id=observation_id, delete_flag=False), Observation
        ).all()
    else:
        observations = apply_race_filter(
            Observation.query.filter_by(delete_flag=False), Observation
        ).all()

    data = [observation.to_dict() for observation in observations]

    draw = request.args.get('draw', 1, type=int)
    recordsTotal = len(observations)
    recordsFiltered = len(observations)

    return jsonify({
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    })

@observation_bp.route('/<observation_id>', methods=['PUT'])
@login_required
def api_update_observation(observation_id):
    """Update an existing observation"""
    try:
        data = request.get_json()['data'][observation_id]  # DataTables Editor sends data in this format
        data.pop('race_id', None)

        cleaned_data = handle_date_fields(data)

        observation = apply_race_filter(
            Observation.query.filter_by(id=observation_id), Observation
        ).first()
        if observation is None:
            return jsonify({'error': 'Observation not found'}), 404

        _race, err = require_writable_race_for_row(observation)
        if err is not None:
            return err
        
        # Update the observation
        for key, value in cleaned_data.items():
            setattr(observation, key, value)
        db.session.add(observation)
        db.session.commit()

        send_observation_notification('edit_observation', observation.to_dict())

        return jsonify({
            'data': [observation.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500


@observation_bp.route('/<observation_id>', methods=['DELETE'])
@login_required
def api_delete_observation(observation_id):
    """soft Delete an existing observation"""
    try:
        observation = apply_race_filter(
            Observation.query.filter_by(id=observation_id, delete_flag=False), Observation
        ).first()
        if observation is None:
            return jsonify({'error': 'Observation not found'}), 404

        _race, err = require_writable_race_for_row(observation)
        if err is not None:
            return err
        
        observation.delete_flag = True
        db.session.commit()

        send_observation_notification('remove_observation', observation.to_dict())

        return jsonify({
            'data': [observation.to_dict()]
        })

    except (TypeError, KeyError, ValueError):
        db.session.rollback()
        return jsonify({'error': 'Invalid request payload.'}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unexpected server error.'}), 500
