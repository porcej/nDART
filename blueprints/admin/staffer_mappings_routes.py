from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import StafferAssignmentMapping, Assignment
from . import admin_bp
from .utils import admin_required


@admin_bp.route('/staffer-mappings')
@login_required
@admin_required
def staffer_mappings():
    """Display staffer assignment mappings."""
    mappings = StafferAssignmentMapping.query.order_by(StafferAssignmentMapping.imported_name).all()
    assignments = Assignment.query.filter_by(enabled=True).order_by(Assignment.name).all()
    
    return render_template('admin/staffer_mappings.html',
                         mappings=mappings,
                         assignments=assignments,
                         username=current_user.name,
                         is_admin=True,
                         is_manager=current_user.is_manager)


@admin_bp.route('/staffer-mappings/<mapping_id>', methods=['GET'])
@login_required
@admin_required
def get_staffer_mapping(mapping_id):
    """Get a single mapping by ID."""
    mapping = StafferAssignmentMapping.query.get(mapping_id)
    if not mapping:
        return jsonify({'error': 'Mapping not found'}), 404
    return jsonify(mapping.to_dict())


@admin_bp.route('/staffer-mappings', methods=['POST'])
@login_required
@admin_required
def create_staffer_mapping():
    """Create a new mapping."""
    try:
        data = request.get_json()
        
        imported_name = data.get('imported_name')
        imported_short_code = data.get('imported_short_code')
        assignment_id = data.get('assignment_id')
        
        # Validate that at least one identifier is provided
        if not imported_name and not imported_short_code:
            return jsonify({'error': 'Either imported_name or imported_short_code must be provided'}), 400
        
        # Create manual mapping
        mapping = StafferAssignmentMapping.create_or_update_mapping(
            imported_name=imported_name,
            imported_short_code=imported_short_code,
            assignment_id=assignment_id if assignment_id else None,
            is_manual=True
        )
        
        return jsonify({
            'success': 'Mapping created successfully',
            'mapping': mapping.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/staffer-mappings/<mapping_id>', methods=['PUT'])
@login_required
@admin_required
def update_staffer_mapping(mapping_id):
    """Update an existing mapping."""
    try:
        mapping = StafferAssignmentMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'imported_name' in data:
            mapping.imported_name = data['imported_name']
        if 'imported_short_code' in data:
            mapping.imported_short_code = data['imported_short_code']
        if 'assignment_id' in data:
            mapping.assignment_id = data['assignment_id'] if data['assignment_id'] else None
        
        # Mark as manual override
        mapping.is_manual_override = True
        
        from datetime import datetime, UTC
        mapping.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        return jsonify({
            'success': 'Mapping updated successfully',
            'mapping': mapping.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/staffer-mappings/<mapping_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_staffer_mapping(mapping_id):
    """Delete a mapping."""
    try:
        mapping = StafferAssignmentMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        db.session.delete(mapping)
        db.session.commit()
        
        return jsonify({
            'success': 'Mapping deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

