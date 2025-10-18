#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example Configuration File for nDART Application

This is a template configuration file. Copy this to config.py and modify
the values according to your environment.

DO NOT commit config.py with sensitive information!
"""

import os
from pathlib import Path

# Get the base directory
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class with common settings."""
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "db", "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security - CHANGE THIS IN PRODUCTION!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHANGE-THIS-SECRET-KEY'
    
    # Application Settings
    HOST = os.environ.get('MED_TRACKER_HOST') or '0.0.0.0'
    PORT = int(os.environ.get('FLASK_PORT') or 9091)
    
    # Logging Configuration
    LOGGING_PATH = os.environ.get('LOGGING_PATH') or os.path.join(basedir, 'logs')
    LOGGING_LEVEL = int(os.environ.get('LOGGING_LEVEL') or 20)  # INFO level
    
    # SocketIO Configuration
    ASYNC_MODE = os.environ.get('ASYNC_MODE') or None  # Auto-detect best mode
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)  # 16MB
    
    # Session Configuration
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL') or 'memory://'
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure directories exist
        os.makedirs(Config.LOGGING_PATH, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')), exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""
    
    DEBUG = True
    LOGGING_LEVEL = 10  # DEBUG level
    
    # Development-specific settings
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for development


class ProductionConfig(Config):
    """Production configuration with security optimizations."""
    
    DEBUG = False
    LOGGING_LEVEL = int(os.environ.get('LOGGING_LEVEL') or 30)  # WARNING level
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 1800  # 30 minutes
    
    # Rate limiting
    RATELIMIT_ENABLED = True


class TestingConfig(Config):
    """Testing configuration for unit tests."""
    
    TESTING = True
    DEBUG = True
    LOGGING_LEVEL = 50  # CRITICAL level (suppress most logs)
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for testing
    RATELIMIT_ENABLED = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
