from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import ObservationsCategory
from extensions import db

from .utils import send_update_notification, handle_date_fields

observation_category_bp = Blueprint('observation_category_bp', __name__, url_prefix='/observation_categories')

@observation_category_bp.route('', methods=['POST'])
@observation_category_bp.route('/', methods=['POST'])
@login_required
def api_create_observation_category():
    """Create a new observation category"""
    try:
        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        # Create a new observation category
        new_observation_category = ObservationsCategory(**cleaned_data)
        db.session.add(new_observation_category)
        db.session.commit()

        send_update_notification('observation_category_update')

        return jsonify({
            'data': [new_observation_category.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@observation_category_bp.route('', methods=['GET']) 
@observation_category_bp.route('/', methods=['GET'])
@observation_category_bp.route('/<observation_category_id>', methods=['GET'])
@login_required
def api_get_observation_categories(observation_category_id=None):
    """
    Return ObservationCategory data as a JSON in a format compatible with DataTables.
    For a basic approact (client-side processing), we'll return all rows
    """
    if observation_category_id is not None:
        observation_categories = ObservationsCategory.query.filter_by(id=observation_category_id, delete_flag=False).all()
    else:
        observation_categories = ObservationsCategory.query.filter_by(delete_flag=False).all()

    data = [observation_category.to_dict() for observation_category in observation_categories]

    draw = request.args.get('draw', 1, type=int)
    recordsTotal = len(observation_categories)
    recordsFiltered = len(observation_categories)

    return jsonify({
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    })

@observation_category_bp.route('/<observation_category_id>', methods=['PUT'])
@login_required
def api_update_observation_category(observation_category_id):
    """Update an existing observation category"""
    try:
        data = request.get_json()['data'][observation_category_id]  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        observation_category = ObservationsCategory.query.filter_by(id=observation_category_id).first()
        if observation_category is None:
            return jsonify({'error': 'Observation category not found'}), 404
        
        # Update the event
        for key, value in cleaned_data.items():
            setattr(observation_category, key, value)
        db.session.add(observation_category)
        db.session.commit()

        send_update_notification('observation_category_update')

        return jsonify({
            'data': [observation_category.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@observation_category_bp.route('/<observation_category_id>', methods=['DELETE'])
@login_required
def api_delete_observation_category(observation_category_id):
    """soft Delete an existing observation category"""
    try:
        observation_category = ObservationsCategory.query.filter_by(id=observation_category_id, delete_flag=False).first()
        if observation_category is None:
            return jsonify({'error': 'Observation category not found'}), 404
        
        observation_category.delete_flag = True
        db.session.commit()

        send_update_notification('observation_category_update')

        return jsonify({
            'data': [observation_category.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
