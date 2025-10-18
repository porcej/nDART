#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI Application Entry Point for nDART

This module provides the WSGI application entry point for production deployment
with Gunicorn + eventlet for Flask-SocketIO support.

Usage:
    gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:9091 wsgi:app
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import socketio

# Create the Flask application
app = create_app()

# Initialize the application (this includes SocketIO setup)
# The init_app function is empty, so we just need the app
# SocketIO will be handled by Gunicorn with eventlet worker

# Export the Flask app for WSGI
application = app

if __name__ == "__main__":
    # This is for development only
    socketio.run(app, debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])