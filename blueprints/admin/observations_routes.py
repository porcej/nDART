from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db, socketio
from models import Observation, ObservationsCategory, Assignment
from datetime import datetime, UTC
from . import admin_bp
from .utils import admin_required
import pandas as pd
import json
from io import BytesIO

# ---------------
# Observations Management
# ---------------
@admin_bp.route('/observations')
@login_required
@admin_required
def observations():
    """Display observations management page."""
    observations = Observation.query.filter_by(delete_flag=False).order_by(Observation.time.desc()).all()
    categories = ObservationsCategory.query.filter_by(enabled=True).all()
    assignments = Assignment.query.filter_by(enabled=True).all()
    
    return render_template('admin/observations.html', 
                         observations=observations, 
                         categories=categories, 
                         assignments=assignments,
                         username=current_user.name, 
                         is_admin=True, 
                         is_manager=current_user.is_manager)

@admin_bp.route('/observations/export')
@login_required
@admin_required
def export_observations():
    """Export all observations to CSV."""
    try:
        observations = Observation.query.filter_by(delete_flag=False).all()
        
        # Create DataFrame
        data = []
        for observation in observations:
            data.append({
                'ID': observation.id,
                'Time': observation.time.strftime('%Y-%m-%d %H:%M:%S') if observation.time else '',
                'Bib': observation.bib or '',
                'Reporter': observation.reporter.name if observation.reporter else '',
                'Category': observation.category.name if observation.category else '',
                'Location': observation.location or '',
                'Notes': observation.notes or ''
            })
        
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Emit SocketIO event for export
        socketio.emit('observations_exported', {
            'count': len(observations),
            'filename': f'observations_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }, namespace='/api')
        
        # Return CSV file
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'observations_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        flash(f'Error exporting observations: {str(e)}', 'error')
        return redirect(url_for('admin.observations'))

@admin_bp.route('/observations/import', methods=['POST'])
@login_required
@admin_required
def import_observations():
    """Import observations from CSV file."""
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin.observations'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.observations'))
        
        if not file.filename.endswith('.csv'):
            flash('Please select a CSV file', 'error')
            return redirect(url_for('admin.observations'))
        
        # Read CSV
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = ['Time', 'Reporter', 'Category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
            return redirect(url_for('admin.observations'))
        
        imported_observations = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Find category by name
                category = ObservationsCategory.query.filter_by(name=row['Category'], enabled=True).first()
                if not category:
                    errors.append(f'Row {index + 1}: Category "{row["Category"]}" not found')
                    continue
                
                # Find assignment by name
                assignment = Assignment.query.filter_by(name=row['Reporter'], enabled=True).first()
                if not assignment:
                    errors.append(f'Row {index + 1}: Reporter "{row["Reporter"]}" not found')
                    continue
                
                # Parse datetime field
                time = None
                if pd.notna(row['Time']) and row['Time']:
                    time = pd.to_datetime(row['Time'])
                
                # Create observation
                observation = Observation(
                    time=time,
                    bib=row.get('Bib', '') if pd.notna(row.get('Bib', '')) else None,
                    reporter_id=assignment.id,
                    category_id=category.id,
                    location=row.get('Location', '') if pd.notna(row.get('Location', '')) else None,
                    notes=row.get('Notes', '') if pd.notna(row.get('Notes', '')) else None
                )
                
                imported_observations.append(observation)
                
            except Exception as e:
                errors.append(f'Row {index + 1}: {str(e)}')
                continue
        
        if errors:
            db.session.rollback()
            flash(f'Import failed. No observations were created. Errors: {"; ".join(errors[:5])}', 'warning')
            socketio.emit('observations_imported', {
                'count': 0,
                'errors': errors[:5],
                'success': False
            }, namespace='/api')
        else:
            if imported_observations:
                db.session.add_all(imported_observations)
                db.session.commit()
            flash(f'Successfully imported {len(imported_observations)} observations', 'success')
            socketio.emit('observations_imported', {
                'count': len(imported_observations),
                'success': True
            }, namespace='/api')
        
        return redirect(url_for('admin.observations'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing observations: {str(e)}', 'error')
        return redirect(url_for('admin.observations'))

@admin_bp.route('/observations/clear', methods=['POST'])
@login_required
@admin_required
def clear_observations():
    """Clear all observations."""
    try:
        # Get count before deletion
        observations_count = Observation.query.count()
        
        # Delete all observations
        Observation.query.delete()
        db.session.commit()
        
        # Emit SocketIO event for clear
        socketio.emit('observations_cleared', {
            'count': observations_count
        }, namespace='/api')
        
        flash(f'Successfully cleared {observations_count} observations', 'success')
        return redirect(url_for('admin.observations'))
        
    except Exception as e:
        flash(f'Error clearing observations: {str(e)}', 'error')
        return redirect(url_for('admin.observations'))

@admin_bp.route('/observations/<id>')
@login_required
@admin_required
def get_observation(id):
    """Get a single observation by UUID."""
    observation = Observation.query.get_or_404(id)
    return jsonify(observation.to_dict())

@admin_bp.route('/observations/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_observation(id):
    """Delete a single observation by UUID."""
    try:
        observation = Observation.query.get_or_404(id)
        observation.delete_flag = True
        db.session.commit()
        return jsonify({'success': 'Observation deleted successfully.'})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete observation.'}), 400
