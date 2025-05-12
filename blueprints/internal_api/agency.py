from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Agency
from extensions import db

from .utils import send_update_notification, handle_date_fields

agency_bp = Blueprint('agency_bp', __name__, url_prefix='/agencies')

@agency_bp.route('', methods=['POST'])
@agency_bp.route('/', methods=['POST'])
@login_required
def api_create_agency():
    """Create a new agency"""
    try:
        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        # Create a new agency
        new_agency = Agency(**cleaned_data)
        db.session.add(new_agency)
        db.session.commit()

        send_update_notification('agency_update')

        return jsonify({
            'data': [new_agency.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@agency_bp.route('', methods=['GET'])
@agency_bp.route('/', methods=['GET'])
@agency_bp.route('/<agency_id>', methods=['GET'])
@login_required
def api_get_agencies(agency_id=None):
    """
    Return Agency data as a JSON in a format compatible with DataTables.
    For a basic approact (client-side processing), we'll return all rows
    """
    if agency_id is not None:
        agencies = Agency.query.filter_by(id=agency_id, delete_flag=False).all()
    else:
        agencies = Agency.query.filter_by(delete_flag=False).all()

    data = [agency.to_dict() for agency in agencies]

    draw = request.args.get('draw', 1, type=int)
    recordsTotal = len(agencies)
    recordsFiltered = len(agencies)

    return jsonify({
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    })

@agency_bp.route('/<agency_id>', methods=['PUT'])
@login_required
def api_update_agency(agency_id):
    """Update an existing agency"""
    try:
        data = request.get_json()['data'][agency_id]  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        agency = Agency.query.filter_by(id=agency_id).first()
        if agency is None:
            return jsonify({'error': 'Agency not found'}), 404
        
        # Update the agency
        for key, value in cleaned_data.items():
            setattr(agency, key, value)
        db.session.add(agency)
        db.session.commit()

        send_update_notification('agency_update')

        return jsonify({
            'data': [agency.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@agency_bp.route('/<agency_id>', methods=['DELETE'])
@login_required
def api_delete_agency(agency_id):
    """soft Delete an existing agency"""
    try:
        agency = Agency.query.filter_by(id=agency_id, delete_flag=False).first()
        if agency is None:
            return jsonify({'error': 'Agency not found'}), 404
        
        agency.delete_flag = True
        db.session.commit()

        send_update_notification('agency_update')

        return jsonify({
            'data': [agency.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
