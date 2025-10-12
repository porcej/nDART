"""
Service for communicating with the ARO Staffer Database API

This service handles all external API calls to the staffer database
for status report updates.
"""

import requests
from models import AppSettings, Assignment, StationStatus, StafferAROVolunteer, StafferAssignmentMapping
from extensions import db
from datetime import datetime


class StafferAPIError(Exception):
    """Custom exception for Staffer API errors"""
    pass


def get_staffer_api_config():
    """Get the API configuration from settings"""
    api_url = AppSettings.get_setting('staffer_api_url', 'http://localhost:8091/public-api/v1')
    api_key = AppSettings.get_setting('staffer_api_key', '')
    
    if not api_key:
        raise StafferAPIError('Staffer API key not configured')
    
    return {
        'base_url': api_url.rstrip('/'),
        'api_key': api_key
    }


def get_api_headers(api_key):
    """Generate headers for API requests"""
    return {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'Accept': 'application/json'
    }


def test_staffer_api_connection():
    """Test connection to the staffer API"""
    try:
        config = get_staffer_api_config()
        headers = get_api_headers(config['api_key'])
        
        details = []
        
        # Try the health endpoint first
        try:
            response = requests.get(
                f"{config['base_url']}/health",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                details.append('✓ Health endpoint: OK')
                try:
                    health_data = response.json()
                    if 'status' in health_data:
                        details.append(f"  Status: {health_data['status']}")
                except:
                    pass
                
                return {
                    'success': True,
                    'details': '\n'.join(details)
                }
            elif response.status_code == 401 or response.status_code == 403:
                return {
                    'success': False,
                    'error': f'Authentication failed (HTTP {response.status_code}). Please check your API key.'
                }
            elif response.status_code == 404:
                details.append('⚠ Health endpoint not found (404)')
            else:
                details.append(f'⚠ Health endpoint returned: HTTP {response.status_code}')
                
        except requests.exceptions.RequestException as e:
            details.append(f'⚠ Health endpoint error: {str(e)[:50]}')
        
        # If health fails, try docs endpoint to verify connectivity
        # Docs is at the same level as v1: /public-api/docs
        try:
            # Remove /v1 from base_url if present and add /docs
            base_without_version = config['base_url'].rstrip('/').replace('/v1', '')
            docs_url = f"{base_without_version}/docs"
            
            response = requests.get(
                docs_url,
                timeout=10
            )
            
            if response.status_code == 200:
                details.append(f'✓ Docs endpoint: Reachable')
                details.append('  Note: API is accessible but health endpoint may not be implemented')
                return {
                    'success': True,
                    'details': '\n'.join(details)
                }
            else:
                details.append(f'✗ Docs endpoint: HTTP {response.status_code}')
                
        except requests.exceptions.RequestException as e:
            details.append(f'✗ Docs endpoint error: {str(e)[:50]}')
        
        # If both fail, check basic connectivity
        try:
            # Try a simple request to the base URL
            response = requests.get(
                config['base_url'],
                timeout=10
            )
            details.append(f'✓ Base URL is reachable (HTTP {response.status_code})')
            details.append('  Warning: Standard endpoints may not be configured correctly')
            
            return {
                'success': True,
                'details': '\n'.join(details)
            }
        except:
            pass
        
        return {
            'success': False,
            'error': 'Could not connect to any API endpoints.\n' + '\n'.join(details)
        }
        
    except StafferAPIError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Could not connect to the API. Please check the URL and ensure the service is running.'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Connection timeout. The API is not responding.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def send_status_report_to_staffer(status_report_data, reporter_data=None, status_data=None):
    """
    Send a status report to the staffer database API
    
    Args:
        status_report_data: Dictionary containing status report information
        reporter_data: Optional dictionary containing reporter/assignment information
        status_data: Optional dictionary containing status information
        
    Returns:
        Dictionary with success status and response data or error message
    """
    try:
        config = get_staffer_api_config()
        headers = get_api_headers(config['api_key'])
        
        # Prepare the payload based on the staffer API requirements
        # This structure may need to be adjusted based on actual API documentation
        payload = {
            'timestamp': status_report_data.get('time', datetime.utcnow()).isoformat() if isinstance(status_report_data.get('time'), datetime) else str(status_report_data.get('time')),
            'status_id': status_report_data.get('status_id'),
            'reporter_id': status_report_data.get('reporter_id'),
            'comment': status_report_data.get('comment', ''),
            'source': 'nDART'
        }
        
        # Add reporter information if available
        if reporter_data:
            payload['reporter'] = {
                'id': reporter_data.get('id'),
                'name': reporter_data.get('name'),
                'role': reporter_data.get('role')
            }
        
        # Add status information if available
        if status_data:
            payload['status'] = {
                'id': status_data.get('id'),
                'name': status_data.get('name'),
                'category': status_data.get('category')
            }
        
        # Send the request to the staffer API
        # Adjust the endpoint based on actual API documentation
        response = requests.post(
            f"{config['base_url']}/status-reports",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return {
                'success': True,
                'data': response.json() if response.content else None
            }
        else:
            error_msg = f'API returned status code {response.status_code}'
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
                elif 'error' in error_data:
                    error_msg = error_data['error']
            except:
                pass
            
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
    
    except StafferAPIError as e:
        return {
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Could not connect to the staffer API'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request to staffer API timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def update_status_report_in_staffer(status_report_id, status_report_data, reporter_data=None, status_data=None):
    """
    Update a status report in the staffer database API
    
    Args:
        status_report_id: ID of the status report to update
        status_report_data: Dictionary containing updated status report information
        reporter_data: Optional dictionary containing reporter/assignment information
        status_data: Optional dictionary containing status information
        
    Returns:
        Dictionary with success status and response data or error message
    """
    try:
        config = get_staffer_api_config()
        headers = get_api_headers(config['api_key'])
        
        # Prepare the payload
        payload = {
            'timestamp': status_report_data.get('time', datetime.utcnow()).isoformat() if isinstance(status_report_data.get('time'), datetime) else str(status_report_data.get('time')),
            'status_id': status_report_data.get('status_id'),
            'reporter_id': status_report_data.get('reporter_id'),
            'comment': status_report_data.get('comment', ''),
            'source': 'nDART'
        }
        
        # Add optional data
        if reporter_data:
            payload['reporter'] = reporter_data
        
        if status_data:
            payload['status'] = status_data
        
        # Send the PUT request
        # Adjust the endpoint based on actual API documentation
        response = requests.put(
            f"{config['base_url']}/status-reports/{status_report_id}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 204]:
            return {
                'success': True,
                'data': response.json() if response.content else None
            }
        else:
            error_msg = f'API returned status code {response.status_code}'
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
                elif 'error' in error_data:
                    error_msg = error_data['error']
            except:
                pass
            
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
    
    except StafferAPIError as e:
        return {
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Could not connect to the staffer API'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request to staffer API timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def sync_assignments_to_staffer():
    """
    Sync all enabled assignments from nDART to the staffer database
    
    Returns:
        Dictionary with success status and sync results
    """
    try:
        config = get_staffer_api_config()
        headers = get_api_headers(config['api_key'])
        
        # Start a session to handle cookies and CSRF tokens
        session = requests.Session()
        session.headers.update(headers)
        
        # First, make a GET request to get CSRF token if needed
        try:
            csrf_response = session.get(f"{config['base_url']}/assignments", timeout=10)
            # Check if there's a CSRF token in cookies
            if 'csrf_token' in session.cookies:
                session.headers.update({'X-CSRFToken': session.cookies['csrf_token']})
        except:
            pass  # If CSRF fetching fails, continue anyway
        
        # Get all enabled assignments from nDART
        assignments = Assignment.query.filter_by(enabled=True).all()
        
        synced_count = 0
        failed_count = 0
        errors = []
        
        for assignment in assignments:
            try:
                # Use short_code if available, otherwise use name
                display_name = assignment.short_code if assignment.short_code else assignment.name
                
                payload = {
                    'id': assignment.id,
                    'name': display_name,
                    'full_name': assignment.name,
                    'description': assignment.description or '',
                    'sort_order': assignment.sort_order,
                    'enabled': assignment.enabled,
                    'source': 'nDART'
                }
                
                # Try to create or update the assignment in staffer
                # Use PUT with ID in URL instead of POST
                response = session.put(
                    f"{config['base_url']}/assignments/{assignment.id}",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    synced_count += 1
                else:
                    failed_count += 1
                    error_msg = f"Assignment '{display_name}': HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'message' in error_data:
                            error_msg = f"Assignment '{display_name}': {error_data['message']}"
                        elif 'detail' in error_data:
                            error_msg = f"Assignment '{display_name}': {error_data['detail']}"
                        else:
                            # Include full error response for debugging
                            error_msg = f"Assignment '{display_name}': HTTP {response.status_code} - {error_data}"
                    except:
                        # If we can't parse JSON, include the text response
                        try:
                            error_msg = f"Assignment '{display_name}': HTTP {response.status_code} - {response.text[:100]}"
                        except:
                            pass
                    errors.append(error_msg)
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"Assignment '{assignment.name}': {str(e)}")
        
        result = {
            'success': failed_count == 0,
            'synced': synced_count,
            'failed': failed_count,
            'total': len(assignments)
        }
        
        if errors:
            result['errors'] = errors
        
        return result
        
    except StafferAPIError as e:
        return {
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Could not connect to the staffer API'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request to staffer API timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def sync_station_statuses_to_staffer():
    """
    Sync all enabled station statuses from nDART to the staffer database
    
    Returns:
        Dictionary with success status and sync results
    """
    try:
        config = get_staffer_api_config()
        headers = get_api_headers(config['api_key'])
        
        # Start a session to handle cookies and CSRF tokens
        session = requests.Session()
        session.headers.update(headers)
        
        # First, make a GET request to get CSRF token if needed
        try:
            csrf_response = session.get(f"{config['base_url']}/statuses", timeout=10)
            # Check if there's a CSRF token in cookies
            if 'csrf_token' in session.cookies:
                session.headers.update({'X-CSRFToken': session.cookies['csrf_token']})
        except:
            pass  # If CSRF fetching fails, continue anyway
        
        # Get all enabled station statuses from nDART
        statuses = StationStatus.query.filter_by(enabled=True).all()
        
        synced_count = 0
        failed_count = 0
        errors = []
        
        for status in statuses:
            try:
                payload = {
                    'id': status.id,
                    'name': status.name,
                    'sort_order': status.sort_order,
                    'enabled': status.enabled,
                    'source': 'nDART'
                }
                
                # Try to create or update the status in staffer
                # Use PUT with ID in URL instead of POST
                response = session.put(
                    f"{config['base_url']}/statuses/{status.id}",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    synced_count += 1
                else:
                    failed_count += 1
                    error_msg = f"Status '{status.name}': HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'message' in error_data:
                            error_msg = f"Status '{status.name}': {error_data['message']}"
                        elif 'detail' in error_data:
                            error_msg = f"Status '{status.name}': {error_data['detail']}"
                        else:
                            # Include full error response for debugging
                            error_msg = f"Status '{status.name}': HTTP {response.status_code} - {error_data}"
                    except:
                        # If we can't parse JSON, include the text response
                        try:
                            error_msg = f"Status '{status.name}': HTTP {response.status_code} - {response.text[:100]}"
                        except:
                            pass
                    errors.append(error_msg)
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"Status '{status.name}': {str(e)}")
        
        result = {
            'success': False,
            'synced': synced_count,
            'failed': failed_count,
            'total': len(statuses)
        }
        
        if errors:
            result['errors'] = errors
        
        return result
        
    except StafferAPIError as e:
        return {
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Could not connect to the staffer API'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request to staffer API timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def sync_aro_volunteers_from_staffer():
    """
    Fetch ARO volunteer data from the staffer database and populate the staffer_aro_volunteers table
    
    Returns:
        Dictionary with success status and sync results
    """
    try:
        config = get_staffer_api_config()
        headers = get_api_headers(config['api_key'])
        
        # Fetch ARO status report data
        response = requests.get(
            f"{config['base_url']}/aro-status-report",
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Failed to fetch ARO volunteers: HTTP {response.status_code}'
            }
        
        data = response.json()
        volunteers_data = data.get('data', [])
        
        synced_count = 0
        skipped_count = 0
        failed_count = 0
        errors = []
        
        # Get all assignments for matching
        all_assignments = Assignment.query.all()
        assignment_by_name = {a.name.lower(): a for a in all_assignments}
        assignment_by_short_code = {a.short_code.lower(): a for a in all_assignments if a.short_code}
        
        for volunteer in volunteers_data:
            try:
                # Extract volunteer data
                assignment_name = volunteer.get('assignment')
                assignment_short_code = volunteer.get('assignment_short_code')
                callsign = volunteer.get('callsign')
                email = volunteer.get('email')
                phone_number = volunteer.get('mobile_phone_number')
                name = volunteer.get('name')
                
                # Skip if no callsign (required field)
                if not callsign:
                    skipped_count += 1
                    continue
                
                # Find matching assignment using mapping table first
                assignment_id = None
                
                # Check mapping table first
                mapping = StafferAssignmentMapping.get_mapping(
                    imported_name=assignment_name,
                    imported_short_code=assignment_short_code
                )
                
                if mapping:
                    assignment_id = mapping.assignment_id
                else:
                    # No mapping exists, try to auto-match
                    matched_assignment = None
                    
                    # Try to match by short_code first
                    if assignment_short_code:
                        matched_assignment = assignment_by_short_code.get(assignment_short_code.lower())
                    
                    # If not found, try to match by name
                    if not matched_assignment and assignment_name:
                        matched_assignment = assignment_by_name.get(assignment_name.lower())
                    
                    if matched_assignment:
                        assignment_id = matched_assignment.id
                        
                        # Create automatic mapping (not manual override)
                        StafferAssignmentMapping.create_or_update_mapping(
                            imported_name=assignment_name,
                            imported_short_code=assignment_short_code,
                            assignment_id=assignment_id,
                            is_manual=False
                        )
                
                # Create or update the staffer volunteer record
                # This works even if assignment_id is None
                StafferAROVolunteer.update_or_create_by_callsign(
                    callsign=callsign,
                    assignment_id=assignment_id,
                    staffer_assignment=assignment_name,  # Store the original assignment from staffer
                    short_code=assignment_short_code,
                    email=email,
                    phone_number=phone_number,
                    name=name
                )
                
                synced_count += 1
                
            except Exception as e:
                failed_count += 1
                volunteer_id = volunteer.get('name', 'Unknown')
                errors.append(f"Volunteer '{volunteer_id}': {str(e)}")
        
        result = {
            'success': failed_count == 0,
            'synced': synced_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total': len(volunteers_data)
        }
        
        if errors:
            result['errors'] = errors
        
        return result
        
    except StafferAPIError as e:
        return {
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Could not connect to the staffer API'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request to staffer API timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }
