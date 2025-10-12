# ARO Staffer Database API Integration

This document describes the integration between nDART and the ARO Staffer Database API for automatic status report synchronization.

## Overview

The nDART application can now automatically send status reports to the ARO Staffer Database via its public API. This integration allows for real-time synchronization of status updates between the two systems.

## Features

- **Admin Configuration Interface**: Administrators can configure the API endpoint and authentication key through the web interface
- **Automatic Synchronization**: When enabled, status reports are automatically sent to the staffer database when created or updated
- **Connection Testing**: Test the API connection before enabling synchronization
- **Error Handling**: Failed API calls are logged but do not prevent status reports from being saved locally
- **Secure Storage**: API keys are stored securely in the database with encryption flags

## Configuration

### Web Interface Configuration (Recommended)

1. Log in as an administrator
2. Navigate to **Admin Dashboard** → **Settings**
3. Configure the following settings:
   - **API Endpoint URL**: The base URL for the staffer database API (e.g., `http://localhost:8091/public-api`)
   - **API Key**: Your API authentication key
   - **Enable synchronization**: Toggle to enable/disable automatic synchronization

4. Click **Test Connection** to verify the configuration
5. Click **Save Settings** to apply the changes

### Environment Variables Configuration

You can also configure the API settings using environment variables:

```bash
export STAFFER_API_URL="http://localhost:8091/public-api"
export STAFFER_API_KEY="your-api-key-here"
export STAFFER_API_ENABLED="true"  # or "false" to disable
```

Note: Settings configured via the web interface take precedence over environment variables.

## API Documentation

The ARO Staffer Database API documentation is available at:
```
http://localhost:8091/public-api/docs
```

Make sure the staffer database service is running and accessible before configuring the integration.

## How It Works

### Status Report Creation Flow

1. User creates a new status report in nDART
2. Status report is saved to the local database
3. If API synchronization is enabled:
   - nDART retrieves the API configuration from settings
   - Prepares the status report data with additional context (reporter info, status info)
   - Sends a POST request to the staffer API
   - Logs the result (success or failure)
4. User receives confirmation that the status report was created

### Status Report Update Flow

1. User updates an existing status report in nDART
2. Status report is updated in the local database
3. If API synchronization is enabled:
   - nDART retrieves the API configuration from settings
   - Prepares the updated status report data
   - Sends a PUT request to the staffer API
   - Logs the result (success or failure)
4. User receives confirmation that the status report was updated

## Technical Details

### Database Schema

A new `app_settings` table stores configuration values:

```sql
CREATE TABLE app_settings (
    id VARCHAR(36) PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE
);
```

### API Payload Structure

When sending status reports to the staffer API, the following payload structure is used:

```json
{
    "timestamp": "2025-10-09T10:30:00",
    "status_id": "uuid-of-status",
    "reporter_id": "uuid-of-reporter",
    "comment": "Status report comment",
    "source": "nDART",
    "reporter": {
        "id": "uuid-of-reporter",
        "name": "Reporter Name",
        "role": "Reporter Role"
    },
    "status": {
        "id": "uuid-of-status",
        "name": "Status Name",
        "category": "Status Category"
    }
}
```

### Error Handling

The integration is designed to be non-blocking:
- If the API is unreachable, the status report is still saved locally
- API errors are logged to the console but do not affect the user experience
- Failed synchronizations can be retried manually if needed

### Security Considerations

- API keys are marked as encrypted in the database (frontend displays them as masked)
- All API requests use HTTPS when the staffer API is configured with a secure endpoint
- Authentication uses the `x-api-key` header for API requests
- Same-origin credentials are used for internal API calls

## Troubleshooting

### Connection Test Fails

1. Verify the API endpoint URL is correct
2. Ensure the staffer database service is running
3. Check network connectivity between nDART and the staffer database
4. Verify the API key is valid

### Status Reports Not Syncing

1. Check that synchronization is enabled in settings
2. Review application logs for error messages
3. Test the connection using the "Test Connection" button
4. Verify the API key has the necessary permissions

### API Authentication Errors

1. Verify the API key is correct
2. Check if the API key has expired
3. Ensure the API key has permission to create/update status reports
4. Review the staffer API documentation for authentication requirements

## Development

### Adding New Settings

To add new application settings:

1. Use the `AppSettings` model to create/update settings:

```python
from models import AppSettings

# Create or update a setting
AppSettings.set_setting(
    'setting_key',
    'setting_value',
    description='Description of the setting',
    is_encrypted=False
)

# Retrieve a setting
value = AppSettings.get_setting('setting_key', default='default_value')
```

2. Add UI controls in `templates/admin/settings.html`
3. Update the settings route in `blueprints/admin/settings_routes.py`

### Modifying the API Service

The staffer API service is located at:
```
blueprints/internal_api/staffer_api_service.py
```

Key functions:
- `get_staffer_api_config()`: Retrieves API configuration
- `test_staffer_api_connection()`: Tests API connectivity
- `send_status_report_to_staffer()`: Sends new status reports
- `update_status_report_in_staffer()`: Updates existing status reports

## Files Modified/Created

### New Files
- `models/app_settings.py` - AppSettings model
- `blueprints/admin/settings_routes.py` - Settings management routes
- `blueprints/internal_api/staffer_api_service.py` - External API service
- `templates/admin/settings.html` - Settings UI
- `migrations/versions/cf765a671187_added_app_settings_table_for_api_.py` - Database migration

### Modified Files
- `models/__init__.py` - Added AppSettings import
- `blueprints/admin/__init__.py` - Added settings_routes import
- `blueprints/admin/routes.py` - Added AppSettings import
- `blueprints/internal_api/status_reports.py` - Integrated API calls
- `templates/admin/index.html` - Added Settings card
- `config.py` - Added staffer API configuration
- `requirements.txt` - Added requests library
- `wsgi.py` - Fixed import issue

## Future Enhancements

Potential improvements for this integration:

1. **Retry Logic**: Implement automatic retry for failed API calls
2. **Batch Synchronization**: Sync multiple status reports at once
3. **Sync History**: Track synchronization status for each status report
4. **Webhook Support**: Allow the staffer database to push updates to nDART
5. **Advanced Mapping**: Configure field mappings between nDART and staffer database
6. **Multiple Endpoints**: Support multiple external APIs simultaneously
7. **Sync Queue**: Queue failed synchronizations for later retry

## Support

For questions or issues with this integration, please refer to:
- nDART project documentation
- ARO Staffer Database API documentation at `http://localhost:8091/public-api/docs`
- Project maintainers

---

Last Updated: October 9, 2025

