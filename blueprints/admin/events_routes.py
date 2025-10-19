from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db, socketio
from models import Event, Agency, Assignment
from datetime import datetime, UTC
from . import admin_bp
from .utils import admin_required
import pandas as pd
import json
from io import BytesIO

# ---------------
# Events Management
# ---------------
@admin_bp.route('/events')
@login_required
@admin_required
def events():
    """Display events management page."""
    events = Event.query.filter_by(delete_flag=False).order_by(Event.time_in.desc()).all()
    agencies = Agency.query.filter_by(enabled=True).all()
    assignments = Assignment.query.filter_by(enabled=True).all()
    
    return render_template('admin/events.html', 
                         events=events, 
                         agencies=agencies, 
                         assignments=assignments,
                         username=current_user.name, 
                         is_admin=True, 
                         is_manager=current_user.is_manager)

@admin_bp.route('/events/export')
@login_required
@admin_required
def export_events():
    """Export all events to CSV."""
    try:
        events = Event.query.filter_by(delete_flag=False).all()
        
        # Create DataFrame
        data = []
        for event in events:
            data.append({
                'ID': event.id,
                'Event ID': event.event_id,
                'Time In': event.time_in.strftime('%Y-%m-%d %H:%M:%S') if event.time_in else '',
                'Bib': event.bib or '',
                'Reporter': event.reporter.name if event.reporter else '',
                'Location': event.location or '',
                'Agency': event.agency.name if event.agency else '',
                'Agency Notified': event.agency_notified.strftime('%Y-%m-%d %H:%M:%S') if event.agency_notified else '',
                'Agency Arrival': event.agency_arrival.strftime('%Y-%m-%d %H:%M:%S') if event.agency_arrival else '',
                'Resolved': event.resolved.strftime('%Y-%m-%d %H:%M:%S') if event.resolved else '',
                'Notes': event.notes or ''
            })
        
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Emit SocketIO event for export
        socketio.emit('events_exported', {
            'count': len(events),
            'filename': f'events_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }, namespace='/api')
        
        # Return CSV file
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'events_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        flash(f'Error exporting events: {str(e)}', 'error')
        return redirect(url_for('admin.events'))

@admin_bp.route('/events/import', methods=['POST'])
@login_required
@admin_required
def import_events():
    """Import events from CSV file."""
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin.events'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.events'))
        
        if not file.filename.endswith('.csv'):
            flash('Please select a CSV file', 'error')
            return redirect(url_for('admin.events'))
        
        # Read CSV
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = ['Time In', 'Bib', 'Reporter', 'Location', 'Agency']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
            return redirect(url_for('admin.events'))
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Find agency by name
                agency = Agency.query.filter_by(name=row['Agency'], enabled=True).first()
                if not agency:
                    errors.append(f'Row {index + 1}: Agency "{row["Agency"]}" not found')
                    continue
                
                # Find assignment by name
                assignment = Assignment.query.filter_by(name=row['Reporter'], enabled=True).first()
                if not assignment:
                    errors.append(f'Row {index + 1}: Reporter "{row["Reporter"]}" not found')
                    continue
                
                # Parse datetime fields
                time_in = None
                if pd.notna(row['Time In']) and row['Time In']:
                    time_in = pd.to_datetime(row['Time In'])
                
                agency_notified = None
                if pd.notna(row.get('Agency Notified', '')) and row.get('Agency Notified', ''):
                    agency_notified = pd.to_datetime(row['Agency Notified'])
                
                agency_arrival = None
                if pd.notna(row.get('Agency Arrival', '')) and row.get('Agency Arrival', ''):
                    agency_arrival = pd.to_datetime(row['Agency Arrival'])
                
                resolved = None
                if pd.notna(row.get('Resolved', '')) and row.get('Resolved', ''):
                    resolved = pd.to_datetime(row['Resolved'])
                
                # Create event
                event = Event(
                    time_in=time_in,
                    bib=row['Bib'] if pd.notna(row['Bib']) else None,
                    reporter_id=assignment.id,
                    location=row['Location'] if pd.notna(row['Location']) else None,
                    agency_id=agency.id,
                    agency_notified=agency_notified,
                    agency_arrival=agency_arrival,
                    resolved=resolved,
                    notes=row.get('Notes', '') if pd.notna(row.get('Notes', '')) else None
                )
                
                db.session.add(event)
                imported_count += 1
                
            except Exception as e:
                errors.append(f'Row {index + 1}: {str(e)}')
                continue
        
        db.session.commit()
        
        if errors:
            flash(f'Imported {imported_count} events. Errors: {"; ".join(errors[:5])}', 'warning')
            socketio.emit('events_imported', {
                'count': imported_count,
                'errors': errors[:5],
                'success': False
            }, namespace='/api')
        else:
            flash(f'Successfully imported {imported_count} events', 'success')
            socketio.emit('events_imported', {
                'count': imported_count,
                'success': True
            }, namespace='/api')
        
        return redirect(url_for('admin.events'))
        
    except Exception as e:
        flash(f'Error importing events: {str(e)}', 'error')
        return redirect(url_for('admin.events'))

@admin_bp.route('/events/clear', methods=['POST'])
@login_required
@admin_required
def clear_events():
    """Clear all events."""
    try:
        # Get count before deletion
        events_count = Event.query.count()
        
        # Delete all events
        Event.query.delete()
        db.session.commit()
        
        # Emit SocketIO event for clear
        socketio.emit('events_cleared', {
            'count': events_count
        }, namespace='/api')
        
        flash(f'Successfully cleared {events_count} events', 'success')
        return redirect(url_for('admin.events'))
        
    except Exception as e:
        flash(f'Error clearing events: {str(e)}', 'error')
        return redirect(url_for('admin.events'))

@admin_bp.route('/events/<id>')
@login_required
@admin_required
def get_event(id):
    """Get a single event by UUID."""
    event = Event.query.get_or_404(id)
    return jsonify(event.to_dict())

@admin_bp.route('/events/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_event(id):
    """Delete a single event by UUID."""
    try:
        event = Event.query.get_or_404(id)
        event.delete_flag = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Event deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
