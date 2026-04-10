from collections import Counter

import pandas as pd
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

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

def _assignment_clean_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def _assignment_clean_int(val, default=0):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def _assignment_clean_bool(val, default=True):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return bool(int(val))
    s = str(val).strip().lower()
    if s in ('true', '1', 'yes', 'y'):
        return True
    if s in ('false', '0', 'no', 'n'):
        return False
    return default


@admin_bp.route('/assignments/import', methods=['POST'])
@login_required
@admin_required
def import_assignments():
    """Import assignments from Excel."""
    file = request.files['import-file']

    if file.filename.endswith('.xlsx'):
        try:
            df = load_xlsx(file)
            assignment_fields = ['name', 'short_code', 'description', 'sort_order', 'enabled']
            valid_columns = [col for col in df.columns if col in assignment_fields]
            df = df[valid_columns]

            rows = []
            for _, row in df.iterrows():
                data = row.to_dict()
                name = _assignment_clean_str(data.get('name'))
                if not name:
                    continue
                short_code = _assignment_clean_str(data.get('short_code'))
                description = data.get('description')
                if description is not None and isinstance(description, float) and pd.isna(description):
                    description = None
                elif description is not None:
                    description = str(description).strip() or None
                rows.append({
                    'name': name,
                    'short_code': short_code,
                    'description': description,
                    'sort_order': _assignment_clean_int(data.get('sort_order'), 0),
                    'enabled': _assignment_clean_bool(data.get('enabled'), True),
                })

            if not rows:
                return jsonify({
                    'error': 'No valid rows: each imported row needs a non-empty name.',
                }), 400

            errors = []
            names = [r['name'] for r in rows]
            dup_names = sorted({n for n, c in Counter(names).items() if c > 1})
            if dup_names:
                errors.append(
                    'Duplicate name(s) in file: ' + ', '.join(dup_names)
                )

            codes = [r['short_code'] for r in rows if r['short_code']]
            dup_codes = sorted({c for c, n in Counter(codes).items() if n > 1})
            if dup_codes:
                errors.append(
                    'Duplicate short_code(s) in file: ' + ', '.join(dup_codes)
                )

            db_name_hits = sorted({
                r['name'] for r in rows
                if Assignment.query.filter_by(name=r['name']).first()
            })
            if db_name_hits:
                errors.append(
                    'Name(s) already in database: ' + ', '.join(db_name_hits)
                )

            db_code_hits = sorted({
                r['short_code'] for r in rows
                if r['short_code']
                and Assignment.query.filter_by(short_code=r['short_code']).first()
            })
            if db_code_hits:
                errors.append(
                    'Short code(s) already in database: ' + ', '.join(db_code_hits)
                )

            if errors:
                return jsonify({'error': ' '.join(errors)}), 400

            for r in rows:
                db.session.add(Assignment(
                    name=r['name'],
                    short_code=r['short_code'],
                    description=r['description'],
                    sort_order=r['sort_order'],
                    enabled=r['enabled'],
                ))

            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                return jsonify({
                    'error': f'Database constraint violation: {e.orig or e}',
                }), 400

            return jsonify({
                'success': f'{len(rows)} assignment(s) created successfully!',
            }), 200
        except Exception as e:
            db.session.rollback()
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