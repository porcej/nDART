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


from config import Config
from extensions import db, migrate, login_manager, jwt, socketio


from models import Agency, Event, Assignment, Observation, ObservationsCategory

# Import blueprints
# from blueprints.auth import auth_bp
from blueprints.main import main_bp
# from blueprints.chat import chat_bp
# from blueprints.admin import admin_bp
from blueprints.internal_api import internal_api_bp
# from blueprints.public_api import public_api_bp

# Setup some user stuff here
class User(UserMixin):
    def __init__(self, name, id, role, active=True):
        self.id = id
        self.name = name
        self.role = role
        self.active = active

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.active

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role == 'manager'
    

@login_manager.user_loader
def load_user(id):
    return Config.USERS[int(id)]


def create_app(config_class=Config):
    """Create and configure the Flask application using the factory pattern.
    
    Args:
        config_class: Configuration class to use (default: Config)
        
    Returns:
        Flask application instance
    """
    # Initialize the app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints
    # app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    # app.register_blueprint(chat_bp)
    # app.register_blueprint(admin_bp)
    app.register_blueprint(internal_api_bp)
    # app.register_blueprint(internal_api_v2_bp)
    # app.register_blueprint(public_api_bp)

    # Configure Flask-Login
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'

    # Initialize Application Users
    idx = 0
    app.config['USERS'] = []
    app.config['USER_ACCOUNTS'] =  {k.lower(): v for k, v in app.config['USER_ACCOUNTS'].items()}

    for n, u in app.config['USER_ACCOUNTS'].items():

        # Create a userid for each user
        u['id'] = idx

        # Set password if no password is provided
        if (u['password'] is None or u['password'] == ''):
            u['password'] = Config.USER_PASSWORD
        app.config['USERS'].append(User(n, idx, u['role']))
        idx += 1
    
    @login_manager.user_loader
    def load_user(user_id):
        return app.config['USERS'][int(user_id)]
        # # Check if user_id is UUID format or numeric ID
        # if '-' in user_id:  # Likely a UUID
        #     return User.query.filter_by(uuid=user_id).first()
        # else:
        #     try:
        #         return User.query.filter_by(id=int(user_id)).first()
        #     except ValueError:
        #         return None
            
    @app.context_processor
    def utility_processor():
        return {'now': datetime.now()}
    
    return app



def init_app(app):




    # *--------------------------------------------------------------------*
    #         Authentication & User Management
    # *--------------------------------------------------------------------*
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            print("Current user is at login page but is authenticated", file=sys.stderr)
            return redirect(url_for('app_index'))

        username = request.form.get('username')
        password = request.form.get('password')

        if username is not None:
            username = username.lower()

        # If a post request was made, find the user by 
        # filtering for the username
        if request.method == "POST":
            if username in app.config['USER_ACCOUNTS'].keys():
                if password == app.config['USER_ACCOUNTS'][username]['password']:
                    user = app.config['USERS'][app.config['USER_ACCOUNTS'][username]['id']]
                    login_user(user, remember='y')
                    return redirect(url_for('app_index'))
            flash('Invalid username or password', 'error')
            # Redirect the user back to the home
            # (we'll create the home route in a moment)
        return render_template("login.html", aid_stations=app.config['USER_ACCOUNTS'].keys())

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))

    # *====================================================================*
    #         ADMIN
    # *====================================================================*
    # Route for uploading xlsx file and removing all rows
    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin():
        if not current_user.is_admin:
            return redirect(url_for('events'))
        if request.method == 'POST':
            if 'remove-events' in request.form:
                remove_all_rows('events')
                return f'All events removed.'
            elif 'remove-observations' in request.form:
                remove_all_rows('observations')
                return f'All observations removed.'
            else:
                return 'I am not a teapot.'

        return render_template('admin.html', active_page='admin', is_admin=current_user.is_admin)

    # *--------------------------------------------------------------------*
    #         End User Routes (Web Pages)
    # *--------------------------------------------------------------------*
    @app.route('/')
    @login_required
    def app_index():
        return redirect(url_for('main_bp.events'))

    # @app.route('/events')
    # @login_required
    # def events():
    #     return render_template("events.html", active_page='events', is_admin=current_user.is_admin)

    @app.route('/observations')
    @login_required
    def observations():
        return render_template("observations.html", active_page='observations', is_admin=current_user.is_admin)


    # *====================================================================*
    #         Chat
    # *====================================================================*
    @app.route('/chat')
    def chat():
        """Chat room. The user's name and room must be stored in
        the session."""
        name = current_user.name
        room = 'chat'
        # if name == '' or room == '':
        #     return redirect(url_for('.index'))
        return render_template('chat.html', active_page='chat', name=name, room=room, is_admin=current_user.is_admin)



    # *====================================================================*
    #         ADMIN
    # *====================================================================*
    # Route for uploading xlsx file and removing all rows


   


   
        

    # *====================================================================*
    #         SocketIO API
    # *====================================================================*
    # Handler for a message recieved over 'connect' channel
    @socketio.on('connect', namespace="/api")
    def test_connect():
        emit('after connect',  {'data':'Lets dance'})

    def send_sio_msg(msg_type, msg, room=None):
        broadcast = room is None
        socketio.emit(msg_type, namespace='/api')

    # *====================================================================*
    #         SocketIO Chat
    # *====================================================================*
    @socketio.on('joined', namespace='/chat')
    def joined(message):
        """Sent by clients when they enter a room.
        A status message is broadcast to all people in the room."""
        room = 'chat'
        join_room(room)
        emit('status', {'msg': current_user.name + ' has entered the room.'}, room=room)


    @socketio.on('text', namespace='/chat')
    def text(message):
        """Sent by a client when the user entered a new message.
        The message is sent to all people in the room."""
        room = 'chat'
        emit('message', {'msg': current_user.name + ':' + message['msg']}, room=room)


    @socketio.on('left', namespace='/chat')
    def left(message):
        """Sent by clients when they leave a room.
        A status message is broadcast to all people in the room."""
        room = 'chat'
        leave_room(room)
        emit('status', {'msg': current_user.name + ' has left the room.'}, room=room)




if __name__ == '__main__':
    app = create_app()
    init_app(app)
    # socketio_app = init_socketio(app)
    
    # Initialize database tables if needed
    # create_tables(app)
    
    # Run the application
    socketio.run(app, debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
    

    
