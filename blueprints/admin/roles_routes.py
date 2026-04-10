from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db
from models import User, Role, ChatRoom, ChatMessage, StationStatus, Assignment, ObservationsCategory
from datetime import datetime, UTC
from uuid import uuid4
from . import admin_bp
from .utils import admin_required
import pandas as pd
from io import BytesIO

# ---------------
# Role Management
# ---------------
@admin_bp.route('/roles')
@login_required
@admin_required
def roles():
    """Display all roles."""
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles, username=current_user.name, is_admin=True, is_manager=current_user.is_manager)

@admin_bp.route('/roles/<id>')
@login_required
@admin_required
def get_role(id):
    """Get a single role by UUID."""
    role = Role.query.get_or_404(id)
    return jsonify(role.to_dict())

@admin_bp.route('/roles', methods=['POST'])
@login_required
@admin_required
def create_role():
    """Create a new role."""
    try:
        data = request.get_json()
        
        # Check if role name already exists
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Role name already exists'}), 400
            
        # Create new role
        role = Role(
            name=data['name'],
            description=data.get('description', ''),
            active=data.get('active', True)
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'success': 'Role created successfully.',
            'data': role.to_dict(),
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create role.'}), 400

@admin_bp.route('/roles/<id>', methods=['PUT'])
@login_required
@admin_required
def update_role(id):
    """Update an existing role."""
    try:
        role = Role.query.get_or_404(id)
        data = request.get_json()
        
        # Don't allow updating the 'admin' role name
        if role.name == 'admin' and 'name' in data and data['name'] != 'admin':
            return jsonify({'error': 'Cannot rename the admin role'}), 400
            
        # Update fields
        if 'name' in data and data['name'] != role.name:
            # Check if role name is already taken
            existing = Role.query.filter_by(name=data['name']).first()
            if existing and existing.id != role.id:
                return jsonify({'error': 'Role name already exists'}), 400
            role.name = data['name']
            
        if 'description' in data:
            role.description = data['description']
            
        if 'active' in data:
            # Don't allow deactivating the 'admin' role
            if role.name == 'admin' and not data['active']:
                return jsonify({'error': 'Cannot deactivate the admin role'}), 400
            role.active = data['active']
            
        db.session.commit()
        
        return jsonify({
            'success': 'Role updated successfully.',
            'data': role.to_dict(),
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update role.'}), 400

@admin_bp.route('/roles/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_role(id):
    """Delete a role."""
    try:
        role = Role.query.get_or_404(id)
        
        # Don't allow deleting the 'admin' role
        if role.name == 'admin':
            return jsonify({'error': 'Cannot delete the admin role'}), 400
            
        # Check if any users have this role
        if role.users and len(role.users) > 0:
            return jsonify({'error': f'Cannot delete role that is assigned to {len(role.users)} users'}), 400
            
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({'success': 'Role deleted successfully.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete role.'}), 400