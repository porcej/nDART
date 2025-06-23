from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import ObservationsCategory
from . import admin_bp
from .utils import admin_required, export_to_xlsx, save_to_database
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
    return render_template('admin/observations_categories.html', observations_categories=observations_categories, username=current_user.name, is_admin=True, is_manager=current_user.is_manager)

@admin_bp.route('/observations-categories/<id>', methods=['GET'])
@login_required
@admin_required
def get_observations_category(id):
    """Get a single observations category by UUID."""
    observations_category = ObservationsCategory.query.get_or_404(id)
    return jsonify(observations_category.to_dict())

@admin_bp.route('/observations-categories', methods=['POST'])
@login_required
@admin_required
def create_observations_category():
    """Create a new observations category."""
    data = request.get_json()
    observations_category = ObservationsCategory(name=data['name'], description=data['description'], enabled=data['enabled'], sort_order=data['sort_order'])

    db.session.add(observations_category)
    db.session.commit()

    return jsonify(observations_category.to_dict()), 201

@admin_bp.route('/observations-categories/<id>', methods=['PUT'])
@login_required
@admin_required
def update_observations_category(id):
    """Update an existing observations category."""
    data = request.get_json()
    observations_category = ObservationsCategory.query.get_or_404(id)   

    observations_category.name = data['name']
    observations_category.description = data['description']
    observations_category.enabled = data['enabled']
    observations_category.sort_order = data['sort_order']
    db.session.commit()

    return jsonify(observations_category.to_dict()) 

@admin_bp.route('/observations-categories/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_observations_category(id):
    """Delete an existing observations category.""" 
    observations_category = ObservationsCategory.query.get_or_404(id)
    db.session.delete(observations_category)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Observations category deleted successfully'})

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
    file = request.files['observations-categories-file']
    if file.filename.endswith('.xlsx'):
        try:
            df = pd.read_excel(file)
            save_to_database(df, 'observations_categories')
            send_encounter_notification('new_observations_category', 'File Uploaded')
            return 'File uploaded and data loaded into database successfully!'
        except Exception as e:
            return f'Error loading file: {e}'
    else:
        return 'Only xlsx files are allowed!'

@admin_bp.route('/observations-categories/remove-all', methods=['DELETE'])
@login_required
@admin_required
def remove_all_observations_categories():
    """Remove all observations categories from the database."""
    ObservationsCategory.query.delete()
    db.session.commit()
    send_encounter_notification('remove_observations_category', 'File Uploaded')
    return 'All observations categories removed from database successfully!'