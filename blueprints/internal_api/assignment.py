from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Assignment
from extensions import db

from .utils import send_update_notification, handle_date_fields

assignment_bp = Blueprint('assignment_bp', __name__, url_prefix='/assignments')

@assignment_bp.route('', methods=['POST'])
@assignment_bp.route('/', methods=['POST'])
@login_required
def api_create_assignment():
    """Create a new assignment"""
    try:
        data = request.get_json()['data']['0']  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        # Create a new assignment
        new_assignment = Assignment(**cleaned_data)
        db.session.add(new_assignment)
        db.session.commit()

        send_update_notification('assignment_update')

        return jsonify({
            'data': [new_assignment.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@assignment_bp.route('', methods=['GET'])
@assignment_bp.route('/', methods=['GET'])
@assignment_bp.route('/<assignment_id>', methods=['GET'])
@login_required
def api_get_assignments(assignment_id=None):
    """
    Return Assignment data as a JSON in a format compatible with DataTables.
    For a basic approact (client-side processing), we'll return all rows
    """
    if assignment_id is not None:
        assignments = Assignment.query.filter_by(id=assignment_id, delete_flag=False).all()
    else:
        assignments = Assignment.query.filter_by(delete_flag=False).all()

    data = [assignment.to_dict() for assignment in assignments]

    draw = request.args.get('draw', 1, type=int)
    recordsTotal = len(assignments)
    recordsFiltered = len(assignments)

    return jsonify({
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': data
    })

@assignment_bp.route('/<assignment_id>', methods=['PUT'])
@login_required
def api_update_assignment(assignment_id):
    """Update an existing assignment"""
    try:
        data = request.get_json()['data'][assignment_id]  # DataTables Editor sends data in this format

        cleaned_data = handle_date_fields(data)

        assignment = Assignment.query.filter_by(id=assignment_id).first()
        if assignment is None:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Update the event
        for key, value in cleaned_data.items():
            setattr(assignment, key, value)
        db.session.add(assignment)
        db.session.commit()

        send_update_notification('assignment_update')

        return jsonify({
            'data': [assignment.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<assignment_id>', methods=['DELETE'])
@login_required
def api_delete_assignment(assignment_id):
    """soft Delete an existing assignment"""
    try:
        assignment = Assignment.query.filter_by(id=assignment_id, delete_flag=False).first()
        if assignment is None:
            return jsonify({'error': 'Assignment not found'}), 404
        
        assignment.delete_flag = True
        db.session.commit()

        send_update_notification('assignment_update')

        return jsonify({
            'data': [assignment.to_dict()]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
