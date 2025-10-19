from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db
from models import StatusReport, StationStatus, Assignment
from datetime import datetime, UTC
from . import admin_bp
from .utils import admin_required
import pandas as pd
import json
from io import BytesIO

# ---------------
# Status Reports Management
# ---------------
@admin_bp.route('/status-reports')
@login_required
@admin_required
def status_reports():
    """Display status reports management page."""
    status_reports = StatusReport.query.filter_by(delete_flag=False).order_by(StatusReport.time.desc()).all()
    station_statuses = StationStatus.query.filter_by(enabled=True).all()
    assignments = Assignment.query.filter_by(enabled=True).all()
    
    return render_template('admin/status_reports.html', 
                         status_reports=status_reports, 
                         station_statuses=station_statuses, 
                         assignments=assignments,
                         username=current_user.name, 
                         is_admin=True, 
                         is_manager=current_user.is_manager)

@admin_bp.route('/status-reports/export')
@login_required
@admin_required
def export_status_reports():
    """Export all status reports to CSV."""
    try:
        status_reports = StatusReport.query.filter_by(delete_flag=False).all()
        
        # Create DataFrame
        data = []
        for status_report in status_reports:
            data.append({
                'ID': status_report.id,
                'Time': status_report.time.strftime('%Y-%m-%d %H:%M:%S') if status_report.time else '',
                'Reporter': status_report.reporter.name if status_report.reporter else '',
                'Status': status_report.status.name if status_report.status else '',
                'Comment': status_report.comment or ''
            })
        
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Return CSV file
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'status_reports_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        flash(f'Error exporting status reports: {str(e)}', 'error')
        return redirect(url_for('admin.status_reports'))

@admin_bp.route('/status-reports/import', methods=['POST'])
@login_required
@admin_required
def import_status_reports():
    """Import status reports from CSV file."""
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin.status_reports'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.status_reports'))
        
        if not file.filename.endswith('.csv'):
            flash('Please select a CSV file', 'error')
            return redirect(url_for('admin.status_reports'))
        
        # Read CSV
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = ['Time', 'Reporter', 'Status']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
            return redirect(url_for('admin.status_reports'))
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Find station status by name
                station_status = StationStatus.query.filter_by(name=row['Status'], enabled=True).first()
                if not station_status:
                    errors.append(f'Row {index + 1}: Status "{row["Status"]}" not found')
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
                
                # Create status report
                status_report = StatusReport(
                    time=time,
                    reporter_id=assignment.id,
                    status_id=station_status.id,
                    comment=row.get('Comment', '') if pd.notna(row.get('Comment', '')) else None
                )
                
                db.session.add(status_report)
                imported_count += 1
                
            except Exception as e:
                errors.append(f'Row {index + 1}: {str(e)}')
                continue
        
        db.session.commit()
        
        if errors:
            flash(f'Imported {imported_count} status reports. Errors: {"; ".join(errors[:5])}', 'warning')
        else:
            flash(f'Successfully imported {imported_count} status reports', 'success')
        
        return redirect(url_for('admin.status_reports'))
        
    except Exception as e:
        flash(f'Error importing status reports: {str(e)}', 'error')
        return redirect(url_for('admin.status_reports'))

@admin_bp.route('/status-reports/clear', methods=['POST'])
@login_required
@admin_required
def clear_status_reports():
    """Clear all status reports."""
    try:
        # Get count before deletion
        status_reports_count = StatusReport.query.count()
        
        # Delete all status reports
        StatusReport.query.delete()
        db.session.commit()
        
        flash(f'Successfully cleared {status_reports_count} status reports', 'success')
        return redirect(url_for('admin.status_reports'))
        
    except Exception as e:
        flash(f'Error clearing status reports: {str(e)}', 'error')
        return redirect(url_for('admin.status_reports'))

@admin_bp.route('/status-reports/<id>')
@login_required
@admin_required
def get_status_report(id):
    """Get a single status report by UUID."""
    status_report = StatusReport.query.get_or_404(id)
    return jsonify(status_report.to_dict())

@admin_bp.route('/status-reports/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_status_report(id):
    """Delete a single status report by UUID."""
    try:
        status_report = StatusReport.query.get_or_404(id)
        status_report.delete_flag = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Status report deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
