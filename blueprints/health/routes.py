#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Health Check Endpoints for Docker

This module provides health check endpoints suitable for Docker health checks.
It includes checks for database connectivity, external services, and application status.

Changelog:
    - 2025-01-27 - Initial implementation
"""

import os
import time
import requests
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from extensions import db

# Create the health blueprint
health_bp = Blueprint('health_bp', __name__)


def check_database():
    """
    Check database connectivity and basic functionality.
    
    Returns:
        dict: Status information including success boolean and details
    """
    try:
        # Test basic database connection
        db.session.execute(text('SELECT 1'))
        
        # Test a simple query to ensure tables are accessible
        # Try to query a table that should exist, fallback to a basic test
        try:
            result = db.session.execute(text('SELECT COUNT(*) FROM user LIMIT 1'))
            user_count = result.scalar()
        except Exception:
            # If user table doesn't exist, try a different approach
            result = db.session.execute(text('SELECT name FROM sqlite_master WHERE type="table" LIMIT 1'))
            table_exists = result.fetchone() is not None
            user_count = 0 if not table_exists else 'unknown'
        
        return {
            'status': 'healthy',
            'message': 'Database connection successful',
            'details': {
                'connection': True,
                'query_test': True,
                'user_count': user_count
            }
        }
    except Exception as e:
        # For Docker health checks, we'll be more tolerant of database issues
        # This allows the container to start even if database needs initialization
        return {
            'status': 'degraded',
            'message': f'Database connection failed: {str(e)}',
            'details': {
                'connection': False,
                'error': str(e),
                'note': 'Database may need initialization'
            }
        }


def check_staffer_api():
    """
    Check external Staffer API connectivity.
    
    Returns:
        dict: Status information including success boolean and details
    """
    try:
        staffer_api_url = current_app.config.get('STAFFER_API_URL')
        staffer_api_enabled = current_app.config.get('STAFFER_API_ENABLED', 'false').lower() == 'true'
        
        if not staffer_api_enabled:
            return {
                'status': 'disabled',
                'message': 'Staffer API is disabled',
                'details': {
                    'enabled': False,
                    'url': staffer_api_url
                }
            }
        
        if not staffer_api_url:
            return {
                'status': 'unhealthy',
                'message': 'Staffer API URL not configured',
                'details': {
                    'enabled': True,
                    'url': None,
                    'error': 'STAFFER_API_URL not set'
                }
            }
        
        # Test API connectivity with a simple request
        timeout = 5  # 5 second timeout
        response = requests.get(
            f"{staffer_api_url}/health", 
            timeout=timeout,
            headers={'Authorization': f'Bearer {current_app.config.get("STAFFER_API_KEY", "")}'}
        )
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': 'Staffer API connection successful',
                'details': {
                    'enabled': True,
                    'url': staffer_api_url,
                    'response_time': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
            }
        else:
            return {
                'status': 'unhealthy',
                'message': f'Staffer API returned status {response.status_code}',
                'details': {
                    'enabled': True,
                    'url': staffer_api_url,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            }
            
    except requests.exceptions.Timeout:
        return {
            'status': 'unhealthy',
            'message': 'Staffer API request timed out',
            'details': {
                'enabled': True,
                'url': current_app.config.get('STAFFER_API_URL'),
                'error': 'Request timeout'
            }
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'unhealthy',
            'message': 'Staffer API connection failed',
            'details': {
                'enabled': True,
                'url': current_app.config.get('STAFFER_API_URL'),
                'error': 'Connection error'
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Staffer API check failed: {str(e)}',
            'details': {
                'enabled': True,
                'url': current_app.config.get('STAFFER_API_URL'),
                'error': str(e)
            }
        }


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint for Docker.
    
    Returns:
        JSON response with overall health status and component details
    """
    start_time = time.time()
    
    # Perform all health checks
    db_status = check_database()
    staffer_status = check_staffer_api()
    
    # Determine overall health - be more tolerant for Docker
    overall_healthy = (
        db_status['status'] in ['healthy', 'degraded'] and 
        staffer_status['status'] in ['healthy', 'disabled']
    )
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Prepare response
    health_data = {
        'status': 'healthy' if overall_healthy else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'response_time': round(response_time, 3),
        'version': current_app.config.get('VERSION', 'unknown'),
        'environment': 'development' if current_app.config.get('DEBUG') else 'production',
        'components': {
            'database': db_status,
            'staffer_api': staffer_status
        }
    }
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_healthy else 503
    return jsonify(health_data), status_code


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check endpoint for Kubernetes/Docker.
    
    This endpoint checks if the application is ready to receive traffic.
    It performs lighter checks than the full health endpoint.
    
    Returns:
        JSON response with readiness status
    """
    try:
        # Basic database connectivity check
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Application is ready to receive traffic'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Application is not ready: {str(e)}'
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check endpoint for Kubernetes/Docker.
    
    This endpoint checks if the application is alive and running.
    It performs minimal checks to avoid false negatives.
    
    Returns:
        JSON response with liveness status
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Application is alive and running'
    }), 200


@health_bp.route('/health/database', methods=['GET'])
def database_health():
    """
    Database-specific health check endpoint.
    
    Returns:
        JSON response with database health status
    """
    db_status = check_database()
    status_code = 200 if db_status['status'] == 'healthy' else 503
    return jsonify(db_status), status_code


@health_bp.route('/health/staffer', methods=['GET'])
def staffer_health():
    """
    Staffer API-specific health check endpoint.
    
    Returns:
        JSON response with Staffer API health status
    """
    staffer_status = check_staffer_api()
    status_code = 200 if staffer_status['status'] in ['healthy', 'disabled'] else 503
    return jsonify(staffer_status), status_code
