#!/usr/bin/env python
# -*- coding: ascii -*-

"""
App to faciliate Net Control for the Marine Corps Marathon (MCM)

Changelog:
    - 2024-07-11 - Initial Commit
"""

__author__ = "Joseph Porcelli (porcej@gmail.com)"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2025 Joseph Porcelli"
__license__ = "MIT"



from datetime import datetime
from io import BytesIO
import os
import pandas as pd
import re
import sqlite3
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, login_user, logout_user, login_required, UserMixin
from urllib.parse import urlsplit
from werkzeug.utils import secure_filename


from config import Config, get_config
from extensions import db, migrate, login_manager, jwt, socketio
from models import User


from models import Agency, Event, Assignment, Observation, ObservationsCategory

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.chat import chat_bp
from blueprints.admin import admin_bp
from blueprints.internal_api import internal_api_bp
from blueprints.health import health_bp
from blueprints.root import root_bp
from blueprints.socketio_api import socketio_api_bp
# from blueprints.public_api import public_api_bp

def create_app(config_class=None):
    """Create and configure the Flask application using the factory pattern.
    
    Args:
        config_class: Configuration class to use (default: Config)
        
    Returns:
        Flask application instance
    """
    # Select configuration class from environment when not explicitly provided
    if config_class is None:
        config_class = get_config()

    # Initialize the app
    app = Flask(__name__)
    app.config.from_object(config_class)
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints
    app.register_blueprint(root_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(internal_api_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(socketio_api_bp)
    # app.register_blueprint(internal_api_v2_bp)
    # app.register_blueprint(public_api_bp)

    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        # Check if user_id is UUID format or numeric ID
        if '-' in user_id:  # Likely a UUID
            return User.query.filter_by(id=user_id).first()
        else:
            return None
            
    @app.context_processor
    def utility_processor():
        return {'now': datetime.now()}
    
    return app



def init_app(app):
    """
    Initialize application-specific functionality.
    
    This function is now empty as all routes have been moved to blueprints.
    It's kept for backward compatibility and potential future use.
    """
    pass




if __name__ == '__main__':
    app = create_app()
    init_app(app)
    # socketio_app = init_socketio(app)
    
    # Initialize database tables if needed
    # create_tables(app)
    
    # Run the application
    socketio.run(app, debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
    

    
