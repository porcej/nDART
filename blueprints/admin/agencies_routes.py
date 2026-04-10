from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from extensions import db
from models import Agency
from . import admin_bp
from .utils import admin_required, export_to_xlsx, load_xlsx

# --------------------
# Agency Management
# --------------------
@admin_bp.route('/agencies', methods=['GET'])
@login_required
@admin_required
def agencies():
    """Display all agencies."""
    agencies = Agency.query.all()
    return render_template('admin/agencies.html', agencies=agencies)

@admin_bp.route('/agencies/<id>', methods=['GET'])
@login_required
@admin_required
def get_agency(id):
    """Get a single agency by UUID."""
    agency = Agency.query.get_or_404(id)
    return jsonify(agency.to_dict())

@admin_bp.route('/agencies', methods=['POST'])
@admin_bp.route('/agencies/', methods=['POST'])
@login_required
@admin_required
def create_agency():
    """Create a new agency."""
    try:
        data = request.get_json()
        
        # Create new agency
        agency = Agency(
            name=data['name'],
            description=data.get('description', ''),
            sort_order=data.get('sort_order', 0),
            enabled=data.get('enabled', True)
        )
        
        db.session.add(agency)
        db.session.commit()
        
        return jsonify({
            'success': 'Agency created successfully.',
            'data': agency.to_dict(),
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create agency.'}), 400

@admin_bp.route('/agencies/<id>', methods=['PUT'])
@login_required
@admin_required
def update_agency(id):
    """Update an existing agency."""
    try:
        agency = Agency.query.get_or_404(id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            agency.name = data['name']
            
        if 'description' in data:
            agency.description = data['description']
            
        if 'sort_order' in data:
            agency.sort_order = data['sort_order']
            
        if 'enabled' in data:
            agency.enabled = data['enabled']
            
        db.session.commit()
        
        return jsonify({
            'success': 'Agency updated successfully.',
            'data': agency.to_dict(),
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update agency.'}), 400

@admin_bp.route('/agencies/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_agency(id):
    """Delete an agency."""
    try:
        agency = Agency.query.get_or_404(id)
        db.session.delete(agency)
        db.session.commit()
        
        return jsonify({'success': 'Agency deleted successfully.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete agency.'}), 400
    
@admin_bp.route('/agencies/export')
@login_required
@admin_required
def export_agencies():
    """Export agencies to Excel."""
    return export_to_xlsx('agencies')

@admin_bp.route('/agencies/import', methods=['POST'])
@login_required
@admin_required
def import_agencies():
    """Import agencies from Excel."""
    file = request.files['import-file']

    if file.filename.endswith('.xlsx'):
        try:
            df = load_xlsx(file)
            # Get valid model fields
            agency_fields = ['name', 'description', 'sort_order', 'enabled']

            # Filter DataFrame to only include valid model fields
            valid_columns = [col for col in df.columns if col in agency_fields]
            
            df = df[valid_columns]
            new_agencies = []
            
            for _, row in df.iterrows():
                data = row.to_dict()
                name = data['name'] if 'name' in data else None
                if not name:
                    continue

                existing_agency = Agency.query.filter_by(name=name).first()

                if existing_agency:
                    continue

                new_agency = Agency(name=name, description=data['description'], sort_order=data['sort_order'], enabled=data['enabled'] if 'enabled' in data else True)
                new_agencies.append(new_agency)

            if new_agencies:
                db.session.add_all(new_agencies)
                db.session.commit()

            return jsonify({'success': f'{len(new_agencies)} agencies created successfully!'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error loading file: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Only xlsx files are allowed!'}), 400

@admin_bp.route('/agencies/remove-all', methods=['DELETE'])
@login_required
@admin_required
def remove_all_agencies():
    """Remove all agencies from the database."""
    Agency.query.delete()
    db.session.commit()
    return jsonify({'success': 'All agencies removed from database successfully!'}), 200
