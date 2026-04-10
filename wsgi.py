#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI Application Entry Point for nDART

This module provides the WSGI application entry point for production deployment
with Gunicorn + gevent for Flask-SocketIO support.

Usage:
    gunicorn -k gevent -w 1 --bind 0.0.0.0:5000 wsgi:application
"""

import os
import sys

# Monkey patch for eventlet compatibility - MUST be done before any other imports
import eventlet
eventlet.monkey_patch()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, init_app
from extensions import socketio

# Create the Flask application
app = create_app()

# Initialize the application (this includes SocketIO setup)
init_app(app)

# Export the Flask app for WSGI
application = app

if __name__ == "__main__":
    # This is for development only
    socketio.run(app, debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])