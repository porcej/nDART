from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import AppSettings
from . import admin_bp
from .utils import admin_required


# ---------------
# Settings Management
# ---------------
@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Display application settings."""
    # Get or create default settings
    staffer_api_url = AppSettings.get_setting('staffer_api_url', 'http://localhost:8091/public-api')
    staffer_api_key = AppSettings.get_setting('staffer_api_key', '')
    
    settings_list = AppSettings.query.all()
    
    return render_template('admin/settings.html', 
                         settings=settings_list,
                         staffer_api_url=staffer_api_url,
                         staffer_api_key=staffer_api_key,
                         username=current_user.name, 
                         is_admin=True, 
                         is_manager=current_user.is_manager)


@admin_bp.route('/settings/get-enabled', methods=['GET'])
@login_required
@admin_required
def get_enabled_status():
    """Get the enabled status of staffer API."""
    enabled = AppSettings.get_setting('staffer_api_enabled', 'false')
    return jsonify({
        'enabled': enabled
    })


@admin_bp.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """Update application settings."""
    try:
        data = request.get_json()
        
        # Update staffer API settings
        if 'staffer_api_url' in data:
            AppSettings.set_setting(
                'staffer_api_url',
                data['staffer_api_url'],
                description='ARO Staffer Database API Base URL',
                is_encrypted=False
            )
        
        if 'staffer_api_key' in data:
            AppSettings.set_setting(
                'staffer_api_key',
                data['staffer_api_key'],
                description='ARO Staffer Database API Key',
                is_encrypted=True
            )
        
        if 'staffer_api_enabled' in data:
            AppSettings.set_setting(
                'staffer_api_enabled',
                data['staffer_api_enabled'],
                description='Enable automatic synchronization with ARO Staffer Database',
                is_encrypted=False
            )
        
        return jsonify({
            'success': 'Settings updated successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/settings/test-connection', methods=['POST'])
@login_required
@admin_required
def test_staffer_connection():
    """Test connection to the staffer API."""
    try:
        from blueprints.internal_api.staffer_api_service import test_staffer_api_connection
        
        result = test_staffer_api_connection()
        
        if result['success']:
            return jsonify({
                'success': 'Connection successful',
                'details': result.get('details', '')
            })
        else:
            return jsonify({
                'error': result.get('error', 'Connection failed')
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/settings/sync-assignments', methods=['POST'])
@login_required
@admin_required
def sync_assignments():
    """Sync assignments to the staffer API."""
    try:
        from blueprints.internal_api.staffer_api_service import sync_assignments_to_staffer
        
        result = sync_assignments_to_staffer()
        
        if result['success']:
            message = f"Successfully synced {result['synced']} of {result['total']} assignments"
            return jsonify({
                'success': message,
                'details': result
            })
        else:
            error_msg = result.get('error', 'Sync failed')
            if 'synced' in result:
                error_msg = f"Synced {result['synced']} of {result['total']} assignments. {result['failed']} failed."
                if 'errors' in result:
                    error_msg += f" Errors: {', '.join(result['errors'][:3])}"
            return jsonify({
                'error': error_msg,
                'details': result
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/settings/sync-statuses', methods=['POST'])
@login_required
@admin_required
def sync_statuses():
    """Sync station statuses to the staffer API."""
    try:
        from blueprints.internal_api.staffer_api_service import sync_station_statuses_to_staffer
        
        result = sync_station_statuses_to_staffer()
        
        if result['success']:
            message = f"Successfully synced {result['synced']} of {result['total']} station statuses"
            return jsonify({
                'success': message,
                'details': result
            })
        else:
            error_msg = result.get('error', 'Sync failed')
            if 'synced' in result:
                error_msg = f"Synced {result['synced']} of {result['total']} statuses. {result['failed']} failed."
                if 'errors' in result:
                    error_msg += f" Errors: {', '.join(result['errors'][:3])}"
            return jsonify({
                'error': error_msg,
                'details': result
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/settings/sync-aro-volunteers', methods=['POST'])
@login_required
@admin_required
def sync_aro_volunteers():
    """Sync ARO volunteer data from the staffer API."""
    try:
        from blueprints.internal_api.staffer_api_service import sync_aro_volunteers_from_staffer
        
        result = sync_aro_volunteers_from_staffer()
        
        if result['success']:
            message = f"Successfully synced {result['synced']} volunteers"
            if result.get('skipped', 0) > 0:
                message += f" ({result['skipped']} skipped - no assignment)"
            return jsonify({
                'success': message,
                'details': result
            })
        else:
            error_msg = result.get('error', 'Sync failed')
            if 'synced' in result:
                error_msg = f"Synced {result['synced']} volunteers. {result['failed']} failed."
                if result.get('skipped', 0) > 0:
                    error_msg += f" {result['skipped']} skipped."
                if 'errors' in result:
                    error_msg += f" Errors: {', '.join(result['errors'][:3])}"
            return jsonify({
                'error': error_msg,
                'details': result
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/settings/import-statuses', methods=['POST'])
@login_required
@admin_required
def import_statuses():
    """Import station statuses from the staffer API."""
    try:
        from blueprints.internal_api.staffer_api_service import import_statuses_from_staffer
        
        result = import_statuses_from_staffer()
        
        if result['success']:
            message = f"Successfully imported {result['imported']} new and updated {result['updated']} existing statuses"
            return jsonify({
                'success': message,
                'details': result
            })
        else:
            error_msg = result.get('error', 'Import failed')
            if 'imported' in result:
                error_msg = f"Imported {result['imported']} new, updated {result['updated']}, {result['failed']} failed."
                if 'errors' in result:
                    error_msg += f" Errors: {', '.join(result['errors'][:3])}"
            return jsonify({
                'error': error_msg,
                'details': result
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

