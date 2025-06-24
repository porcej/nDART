from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Assignment
from . import admin_bp
from .utils import admin_required, export_to_xlsx, load_xlsx

# --------------------
# Assignment Management
# --------------------
@admin_bp.route('/assignments', methods=['GET'])
@login_required
@admin_required
def assignments():
    """Display all assignments."""
    assignments = Assignment.query.all()
    return render_template('admin/assignments.html', assignments=assignments, username=current_user.name, is_admin=True, is_manager=current_user.is_manager)

@admin_bp.route('/assignments/<id>', methods=['GET'])
@login_required
@admin_required
def get_assignment(id):
    """Get a single assignment by UUID."""
    assignment = Assignment.query.get_or_404(id)
    return jsonify(assignment.to_dict())


@admin_bp.route('/assignments', methods=['POST'])
@admin_bp.route('/assignments/', methods=['POST'])
@login_required
@admin_required
def create_assignment():
    """Create a new assignment."""
    data = request.get_json()
    assignment = Assignment(**data)

    db.session.add(assignment)
    db.session.commit()

    return jsonify(assignment.to_dict()), 201

@admin_bp.route('/assignments/<id>', methods=['PUT'])
@login_required
@admin_required
def update_assignment(id):
    """Update an existing assignment."""
    data = request.get_json()
    assignment = Assignment.query.get_or_404(id)
    for key, value in data.items():
        setattr(assignment, key, value)

    db.session.commit()

    return jsonify(assignment.to_dict()), 200

@admin_bp.route('/assignments/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_assignment(id):
    """Delete an assignment."""
    try:
        assignment = Assignment.query.get_or_404(id)
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/assignments/export')
@login_required
@admin_required
def export_assignments():
    """Export assignments to Excel."""
    return export_to_xlsx('assignments')

@admin_bp.route('/assignments/import', methods=['POST'])
@login_required
@admin_required
def import_assignments():
    """Import assignments from Excel."""
    file = request.files['import-file']

    if file.filename.endswith('.xlsx'):
        try:
            df = load_xlsx(file)
            # Get valid model fields
            assignment_fields = ['name', 'description', 'sort_order', 'enabled']

            # Filter DataFrame to only include valid model fields
            valid_columns = [col for col in df.columns if col in assignment_fields]
            
            df = df[valid_columns]
            new_assignment_count = 0
            
            for _, row in df.iterrows():
                data = row.to_dict()
                name = data['name'] if 'name' in data else None
                if not name:
                    continue

                existing_assignment = Assignment.query.filter_by(name=name).first()

                if existing_assignment:
                    continue

                new_assignment = Assignment(name=name, description=data['description'], sort_order=data['sort_order'], enabled=data['enabled'] if 'enabled' in data else True)

                db.session.add(new_assignment)
                db.session.commit()
                new_assignment_count += 1

            return jsonify({'success': f'{new_assignment_count} assignments created successfully!'}), 200
        except Exception as e:
            return jsonify({'error': f'Error loading file: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Only xlsx files are allowed!'}), 400

@admin_bp.route('/assignments/remove-all', methods=['DELETE'])
@login_required
@admin_required
def remove_all_assignments():
    """Remove all assignments from the database."""
    Assignment.query.delete()
    db.session.commit()
    return jsonify({'success': 'All assignments removed from database successfully!'}), 200