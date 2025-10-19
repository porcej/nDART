#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Standalone SocketIO Server for nDART

This script runs Flask-SocketIO directly without WSGI, which is more stable
for SocketIO applications.

Usage:
    python socketio_server.py
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, init_app
from extensions import socketio

# Create the Flask application
app = create_app()

# Initialize the application (this includes SocketIO setup)
init_app(app)

if __name__ == "__main__":
    # Run the SocketIO server directly
    socketio.run(
        app,
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT'],
        allow_unsafe_werkzeug=True
    )
