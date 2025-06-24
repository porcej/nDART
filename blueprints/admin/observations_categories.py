from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import ObservationsCategory
from . import admin_bp
from .utils import admin_required, export_to_xlsx, load_xlsx
import pandas as pd

# -----------------
# Observations Category Management
# -----------------
@admin_bp.route('/observations-categories')
@login_required
@admin_required
def observations_categories():
    """Display all observations categories."""
    observations_categories = ObservationsCategory.query.all()
    return render_template('admin/observations_categories.html',
                           observations_categories=observations_categories,
                           username=current_user.name,
                           is_admin=True,
                           is_manager=current_user.is_manager)

@admin_bp.route('/observations-categories/<id>', methods=['GET'])
@login_required
@admin_required
def get_observations_category(id):
    """Get a single observations category by UUID."""
    observations_category = ObservationsCategory.query.get_or_404(id)
    return jsonify(observations_category.to_dict())

@admin_bp.route('/observations-categories', methods=['POST'])
@admin_bp.route('/observations-categories/', methods=['POST'])
@login_required
@admin_required
def create_observations_category():
    """Create a new observations category."""
    try:
        data = request.get_json()
        observations_category = ObservationsCategory(
            name=data['name'],
            description=data['description'],
            enabled=data['enabled'],
            sort_order=data['sort_order'],
        )

        db.session.add(observations_category)
        db.session.commit()

        return jsonify(observations_category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/observations-categories/<id>', methods=['PUT'])
@login_required
@admin_required
def update_observations_category(id):
    """Update an existing observations category."""
    try:
        data = request.get_json()
        observations_category = ObservationsCategory.query.get_or_404(id)   

        if 'name' in data:
            observations_category.name = data['name']
        if 'description' in data:
            observations_category.description = data['description']
        if 'enabled' in data:
            observations_category.enabled = data['enabled']
        if 'sort_order' in data:
            observations_category.sort_order = data['sort_order']
        db.session.commit()

        return jsonify(observations_category.to_dict()) 
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/observations-categories/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_observations_category(id):
    """Delete an existing observations category.""" 
    try:
        observations_category = ObservationsCategory.query.get_or_404(id)
        db.session.delete(observations_category)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Observations category deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/observations-categories/export')
@login_required
@admin_required
def export_observations_categories():
    """Export observations categories to Excel."""
    return export_to_xlsx('observations_categories')

@admin_bp.route('/observations-categories/import', methods=['POST'])
@login_required
@admin_required
def import_observations_categories():
    """Import observations categories from Excel."""
    file = request.files['import-file']

    if file.filename.endswith('.xlsx'):
        try:
            df = load_xlsx(file)
            # Get valid model fields
            observations_category_fields = ['name', 'description', 'sort_order', 'enabled']

            # Filter DataFrame to only include valid model fields
            valid_columns = [col for col in df.columns if col in observations_category_fields]
            
            df = df[valid_columns]
            new_observations_category_count = 0
            
            for _, row in df.iterrows():
                data = row.to_dict()
                name = data['name'] if 'name' in data else None
                if not name:
                    continue

                existing_observations_category = ObservationsCategory.query.filter_by(name=name).first()

                if existing_observations_category:
                    continue

                new_observations_category = ObservationsCategory(
                    name=name, 
                    sort_order=data['sort_order'] if 'sort_order' in data else 0, 
                    enabled=data['enabled'] if 'enabled' in data else True,
                    description=data['description'] if 'description' in data else None
                )

                db.session.add(new_observations_category)
                db.session.commit()
                new_observations_category_count += 1

            return jsonify({'success': f'{new_observations_category_count} observations categories created successfully!'}), 200
        except Exception as e:
            return jsonify({'error': f'Error loading file: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Only xlsx files are allowed!'}), 400

@admin_bp.route('/observations-categories/remove-all', methods=['DELETE'])
@login_required
@admin_required
def remove_all_observations_categories():
    """Remove all observations categories from the database."""
    
    ObservationsCategory.query.delete()
    db.session.commit()
    return 'All observations categories removed from database successfully!'