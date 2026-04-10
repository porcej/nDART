from collections import Counter

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import StationStatus
from . import admin_bp
from .utils import admin_required, export_to_xlsx, load_xlsx

# --------------------
# Station Status Management
# --------------------
@admin_bp.route('/station-status')
@login_required
@admin_required
def station_status():
    """Display all station statuses."""
    station_statuses = StationStatus.query.all()
    return render_template('admin/station_status.html', 
                         station_statuses=station_statuses,
                         username=current_user.name, 
                         is_admin=True, 
                         is_manager=current_user.is_manager)

@admin_bp.route('/station-status/<id>', methods=['GET'])
@login_required
@admin_required
def get_station_status(id):
    """Get a single station status by UUID."""
    station_status = StationStatus.query.get_or_404(id)
    return jsonify(station_status.to_dict())

@admin_bp.route('/station-status', methods=['POST'])
@admin_bp.route('/station-status/', methods=['POST'])
@login_required
@admin_required
def create_station_status():
    """Create a new station status."""
    try:
        data = request.get_json()
        
        # Create new station status
        station_status = StationStatus(
            name=data['name'],
            sort_order=data.get('sort_order', 0),
            enabled=data.get('enabled', True)
        )
        
        db.session.add(station_status)
        db.session.commit()
        
        return jsonify({
            'success': 'Station status created successfully.',
            'data': station_status.to_dict(),
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create station status.'}), 400

@admin_bp.route('/station-status/<id>', methods=['PUT'])
@login_required
@admin_required
def update_station_status(id):
    """Update an existing station status."""
    try:
        station_status = StationStatus.query.get_or_404(id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            station_status.name = data['name']
            
        if 'sort_order' in data:
            station_status.sort_order = data['sort_order']
            
        if 'enabled' in data:
            station_status.enabled = data['enabled']
            
        db.session.commit()
        
        return jsonify({
            'success': 'Station status updated successfully.',
            'data': station_status.to_dict(),
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update station status.'}), 400

@admin_bp.route('/station-status/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_station_status(id):
    """Delete a station status."""
    try:
        station_status = StationStatus.query.get_or_404(id)
        db.session.delete(station_status)
        db.session.commit()
        
        return jsonify({'success': 'Station status deleted successfully.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete station status.'}), 400

@admin_bp.route('/station-status/export')
@login_required
@admin_required
def export_station_status():
    """Export station statuses to Excel."""
    return export_to_xlsx('station_status')

@admin_bp.route('/station-status/import', methods=['POST'])
@login_required
@admin_required
def import_station_status():
    """Import assignments from Excel."""
    file = request.files['import-file']

    if file.filename.endswith('.xlsx'):
        try:
            df = load_xlsx(file)
            # Get valid model fields
            station_status_fields = ['name', 'sort_order', 'enabled']

            # Filter DataFrame to only include valid model fields
            valid_columns = [col for col in df.columns if col in station_status_fields]
            
            df = df[valid_columns]
            new_station_statuses = []
            normalized_names = []
            
            for _, row in df.iterrows():
                data = row.to_dict()
                name = data['name'] if 'name' in data else None
                if not name:
                    continue
                name = str(name).strip()
                if not name:
                    continue
                normalized_names.append(name)

            duplicate_names = sorted([name for name, count in Counter(normalized_names).items() if count > 1])
            if duplicate_names:
                return jsonify({'error': f'Duplicate name(s) in file: {", ".join(duplicate_names)}'}), 400

            for _, row in df.iterrows():
                data = row.to_dict()
                name = data['name'] if 'name' in data else None
                if not name:
                    continue
                name = str(name).strip()
                if not name:
                    continue

                existing_station_status = StationStatus.query.filter_by(name=name).first()

                if existing_station_status:
                    continue

                new_station_status = StationStatus(name=name, sort_order=data['sort_order'], enabled=data['enabled'] if 'enabled' in data else True)
                new_station_statuses.append(new_station_status)

            if new_station_statuses:
                db.session.add_all(new_station_statuses)
                db.session.commit()

            return jsonify({'success': f'{len(new_station_statuses)} station statuses created successfully!'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error loading file: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Only xlsx files are allowed!'}), 400

@admin_bp.route('/station-status/remove-all', methods=['DELETE'])
@login_required
@admin_required
def remove_all_station_status():
    """Remove all station statuses from the database."""
    StationStatus.query.delete()
    db.session.commit()
    return jsonify({'success': 'All station statuses removed from database successfully!'}), 200