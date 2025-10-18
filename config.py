#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration File for nDART Application

This module contains configuration classes for different environments:
- Development: Local development with debug enabled
- Production: Production deployment with security optimizations
- Testing: Unit testing configuration

Environment Variables:
    DATABASE_URL: Database connection string
    SECRET_KEY: Flask secret key for sessions
    NDART_DEBUG: Enable debug mode (True/False)
    NDART_HOST: Host to bind the application
    FLASK_PORT: Port to run the application
    LOGGING_PATH: Directory for log files
    LOGGING_LEVEL: Logging level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)
    ASYNC_MODE: SocketIO async mode (threading, eventlet, gevent, or None for auto)
    UPLOAD_FOLDER: Directory for file uploads
    MAX_CONTENT_LENGTH: Maximum file upload size in bytes

Changelog:
    - 2024-05-15 - Initial Commit
    - 2025-01-18 - Refactored for production readiness
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
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Application Settings
    HOST = os.environ.get('NDART_HOST') or '0.0.0.0'
    PORT = int(os.environ.get('FLASK_PORT') or 5000)
    
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
    
    # Database for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "db", "dev.db")}'


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
    
    # Database optimizations for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 20,
        'max_overflow': 30,
    }
    
    @classmethod
    def init_app(cls, app):
        """Initialize production app with additional security."""
        Config.init_app(app)
        
        # Validate required environment variables
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        
        if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            raise ValueError("Default SECRET_KEY cannot be used in production")


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


class DockerConfig(Config):
    """Docker-specific configuration."""
    
    # Docker-specific settings
    HOST = '0.0.0.0'
    
    # Ensure proper paths in Docker
    LOGGING_PATH = '/app/logs'
    UPLOAD_FOLDER = '/app/uploads'
    
    # Database path in Docker
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:////app/db/app.db'


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])


# Logging level mapping for reference
LOGGING_LEVELS = {
    'CRITICAL': 50,
    'ERROR': 40,
    'WARNING': 30,
    'INFO': 20,
    'DEBUG': 10,
    'VERBOSE': 1,
    'NOTSET': 0
}