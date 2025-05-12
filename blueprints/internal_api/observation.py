from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Observation
from extensions import db

from .utils import send_observation_notification, handle_date_fields

observation_bp = Blueprint('observation_bp', __name__, url_prefix='/observations')

@observation_bp.route('', methods=['POST'])
@observation_bp.route('/', methods=['POST'])
@login_required
def api_create_observation():
    """Create a new observation"""
    try:
        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        # Create a new observation
        new_observation = Observation(**cleaned_data)
        db.session.add(new_observation)
        db.session.commit()

        send_observation_notification('new_observation', new_observation.to_dict())

        return jsonify({
            'data': [new_observation.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@observation_bp.route('', methods=['GET'])
@observation_bp.route('/', methods=['GET'])
@observation_bp.route('/<observation_id>', methods=['GET'])
@login_required
def api_get_observations(observation_id=None):
    """
    Return Observation data as a JSON in a format compatible with DataTables.
    For a basic approact (client-side processing), we'll return all rows
    """
    if observation_id is not None:
        observations = Observation.query.filter_by(id=observation_id, delete_flag=False).all()
    else:
        observations = Observation.query.filter_by(delete_flag=False).all()

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

        cleaned_data = handle_date_fields(data)

        observation = Observation.query.filter_by(id=observation_id).first()
        if observation is None:
            return jsonify({'error': 'Observation not found'}), 404
        
        # Update the observation
        for key, value in cleaned_data.items():
            setattr(observation, key, value)
        db.session.add(observation)
        db.session.commit()

        send_observation_notification('edit_observation', observation.to_dict())

        return jsonify({
            'data': [observation.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@observation_bp.route('/<observation_id>', methods=['DELETE'])
@login_required
def api_delete_observation(observation_id):
    """soft Delete an existing observation"""
    try:
        observation = Observation.query.filter_by(id=observation_id, delete_flag=False).first()
        if observation is None:
            return jsonify({'error': 'Observation not found'}), 404
        
        observation.delete_flag = True
        db.session.commit()

        send_observation_notification('remove_observation', observation.to_dict())

        return jsonify({
            'data': [observation.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
