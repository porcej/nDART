from collections import Counter

from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Role
from . import admin_bp
from .utils import admin_required, export_to_xlsx, save_to_database, load_xlsx, clean_str, clean_bool


# ---------------
# User Management
# ---------------
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Display all users with filtering options."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=users, roles=roles, username=current_user.name, is_admin=True, is_manager=current_user.is_manager)

@admin_bp.route('/users/<id>')
@login_required
@admin_required
def get_user(id):
    """Get a single user by UUID."""
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

@admin_bp.route('/users', methods=['POST'])
@admin_bp.route('/users/', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Create a new user."""
    try:
        data = request.get_json()
        
        # Check if username already exists
        if User.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        # Create new user
        user = User(
            name=data['name'],
            person=data.get('person', ''),
            active=data.get('active', True)
        )
        
        # Set password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        # Assign ID if provided
        if 'id' in data and data['id']:
            user.id = data['id']
                        
        # Assign roles if provided
        for role_id in data.get('roles', []):
            role = Role.query.get(role_id)
            if role:
                user.add_role(role)
                
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': 'User created successfully.',
            'data': user.to_dict(),
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user.'}), 400

@admin_bp.route('/users/<id>', methods=['PUT'])
@login_required
@admin_required
def update_user(id):
    """Update an existing user."""
    try:
        user = User.query.get_or_404(id)
        data = request.get_json()
        
        # Update basic fields
        if 'name' in data and data['name'] != user.name:
            # Check if new username is already taken
            existing = User.query.filter_by(name=data['name']).first()
            if existing and existing.id != user.id:
                return jsonify({'error': 'Username already exists'}), 400
            user.name = data['name']
            
        if 'person' in data:
            user.person = data['person']
            
        if 'active' in data:
            if current_user.id != user.id:
                user.active = data['active']
            
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
            
        # Update roles
        if 'roles' in data:
            # Clear existing roles
            user.roles = []
            
            # Add new roles
            for role_id in data['roles']:
                role = Role.query.get(role_id)
                if role:
                    user.add_role(role)
                    
        db.session.commit()
        return jsonify({
            'success': 'User updated successfully.',
            'data': user.to_dict(),
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user.'}), 400

@admin_bp.route('/users/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(id):
    """Delete a user."""
    try:
        # Don't allow users to delete themselves
        if id == current_user.id:
            return jsonify({'error': 'You cannot delete your own account'}), 400
            
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': 'User deleted successfully.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user.'}), 400
    
@admin_bp.route('/users/export')
@login_required
@admin_required
def export_users():
    """Export users to Excel."""
    return export_to_xlsx('users')

@admin_bp.route('/users/import', methods=['POST'])
@login_required
@admin_required
def import_users():
    """Import users from Excel."""
    file = request.files['import-file']
    default_password = request.form.get('importPassword') or None

    if file.filename.endswith('.xlsx'):
        try:
            df = load_xlsx(file)
            # Get valid model fields
            roles_fields = [f'is_{role.name.lower().replace(" ", "_")}' for role in Role.query.all()]
            user_fields = ['name', 'person', 'active', 'password'] + roles_fields

            # Filter DataFrame to only include valid model fields
            valid_columns = [col for col in df.columns if col in user_fields]
            
            df = df[valid_columns]
            normalized_names = []
            for _, row in df.iterrows():
                data = row.to_dict()
                name = clean_str(data.get('name'))
                if not name:
                    continue
                normalized_names.append(name)

            duplicate_names = sorted(
                [n for n, c in Counter(normalized_names).items() if c > 1]
            )
            if duplicate_names:
                return jsonify({
                    'error': f'Duplicate username(s) in file: {", ".join(duplicate_names)}',
                }), 400

            new_users = []
            for _, row in df.iterrows():
                data = row.to_dict()
                username = clean_str(data.get('name'))
                if not username:
                    continue

                existing_user = User.query.filter_by(name=username).first()

                if existing_user:
                    continue

                pwd_cell = clean_str(data.get('password'))
                password = pwd_cell if pwd_cell else default_password

                if password in [None, '']:
                    continue

                person = clean_str(data.get('person'))
                active = clean_bool(data.get('active'), False)
                new_user = User(name=username, person=person, active=active)

                for role_field in roles_fields:
                    if role_field in data and clean_bool(data.get(role_field), False):
                        role = Role.query.filter_by(name=role_field.replace('is_', '')).first()
                        if role:
                            new_user.add_role(role)

                if password:
                    new_user.set_password(password)

                new_users.append(new_user)

            if new_users:
                db.session.add_all(new_users)
                db.session.commit()

            return jsonify({'success': f'{len(new_users)} users created successfully!'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error loading file: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Only xlsx files are allowed!'}), 400

@admin_bp.route('/users/remove-all', methods=['DELETE'])
@login_required
@admin_required
def remove_all_users():
    """Remove all users from the database."""
    # Don't allow users to delete themselves
    if current_user.id:
        User.query.filter(User.id != current_user.id).delete()
    else:
        User.query.delete()
    db.session.commit()
    return jsonify({'success': 'All users removed from database successfully!'}), 200


# -----------------
# Helper endpoints
# -----------------
@admin_bp.route('/user-roles')
@login_required
@admin_required
def get_user_roles():
    """Get all users with their assigned roles."""
    users = User.query.all()
    user_roles = []
    
    for user in users:
        user_roles.append({
            'user_id': user.id,
            'user_name': user.name,
            'roles': [{'role_id': role.id, 'role_name': role.name} for role in user.roles]
        })
        
    return jsonify({'success': 'User roles fetched successfully.', 'data': user_roles})