#!/usr/bin/env python
# -*- coding: ascii -*-

"""
App to faciliate Net Control for the Marine Corps Marathon (MCM)

Changelog:
    - 2024-07-11 - Initial Commit
"""

__author__ = "Joseph Porcelli (porcej@gmail.com)"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2024 Joseph Porcelli"
__license__ = "MIT"


from config import Config
from pprint import pprint
import datetime
from io import BytesIO
import os
import pandas as pd
import re
import sqlite3
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import current_user, LoginManager, login_user, logout_user, login_required, UserMixin
from urllib.parse import urlsplit
from werkzeug.utils import secure_filename

from flask_socketio import SocketIO, emit, join_room, leave_room


# Initialize the app
app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.login_view  = 'login'
login_manager.init_app(app)

socketio = SocketIO()
socketio.init_app(app)

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


# *====================================================================*
#         APP CONFIG
# *====================================================================*
idx = 0
Config.USERS = []
for n, u in Config.USER_ACCOUNTS.items():

    # Create a userid for each user
    u['id'] = idx

    # Set password if no password is provided
    if (u['password'] is None or u['password'] == ''):
        u['password'] = Config.USER_PASSWORD
    Config.USERS.append(User(n, idx, u['role']))
    idx += 1

# *====================================================================*
#         INITIALIZE DB & DB access
# *====================================================================*
# This should be a recursive walk for the database path... TODO
if not os.path.exists('db'):
    os.makedirs('db')

# Function to connect to SQLLite Database
def db_connect():
    return sqlite3.connect(Config.DATABASE_PATH)


# Function to create an SQLite database and table to store data
def create_database():
    conn =  db_connect()
    cursor = conn.cursor()

    # Events Table - Holds a list of all events
    cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      time_in TEXT,
                      bib TEXT,
                      reporter TEXT,
                      location TEXT,
                      agency TEXT,
                      agency_notified TEXT,
                      agency_arrival TEXT,
                      resolved TEXT,
                      notes TEXT
                   )''')

    # Add Agency to events table if it isn't already there
    try:
        cursor.execute('''ALTER TABLE events ADD agency TEXT''')
    except Exception as e:
        pass # Its okay, we already have the agency field


    cursor.execute('''CREATE TABLE IF NOT EXISTS observations (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      time TEXT NOT NULL,
                      bib TEXT,
                      location TEXT,
                      category TEXT
                   )''')



    print("Database created!", file=sys.stderr)
    conn.commit()
    conn.close()



# Function to export participant data as a zipped dict
def zip_table(table_name, where_clause=None):
    if where_clause is None:
        where_clause = ""
    else:
        where_clause = f' WHERE {where_clause}'
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
        cursor = conn.cursor()
        select_statement = f'SELECT * FROM {table_name}{where_clause if where_clause else ""}'
        cursor.execute(select_statement)
        rows = cursor.fetchall()
        # Get the column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        # Convert the data to a list of dictionaries
    data_list = []
    for row in rows:
        data_dict = dict(zip(columns, row))
        data_list.append(data_dict)
    return {'data': data_list}

# *====================================================================*
#         ROUTES
# *====================================================================*


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


    # If a post request was made, find the user by 
    # filtering for the username
    if request.method == "POST":
        if username in Config.USER_ACCOUNTS.keys():
            if password == Config.USER_ACCOUNTS[username]['password']:
                user = Config.USERS[Config.USER_ACCOUNTS[username]['id']]
                login_user(user, remember='y')
                return redirect(url_for('app_index'))
        flash('Invalid username or password', 'error')
        # Redirect the user back to the home
        # (we'll create the home route in a moment)
    return render_template("login.html", aid_stations=Config.USER_ACCOUNTS.keys())

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# *--------------------------------------------------------------------*
#         End User Routes (Web Pages)
# *--------------------------------------------------------------------*
@app.route('/')
@login_required
def app_index():
    return redirect(url_for('events'))

@app.route('/events')
@login_required
def events():
    # conn = db_connect()
    # cursor = conn.cursor()
    # conn.close()
    return render_template("events.html")

@app.route('/observations')
@login_required
def observations():
    # conn = db_connect()
    # cursor = conn.cursor()
    # conn.close()
    return render_template("observations.html")


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
    return render_template('chat.html', name=name, room=room, is_admin=current_user.is_admin)



# *====================================================================*
#         ADMIN
# *====================================================================*
# Route for uploading xlsx file and removing all rows



# *====================================================================*
#         API
# *====================================================================*
@app.route('/api/events', methods=['GET', 'POST'])
@app.route('/api/events/', methods=['GET', 'POST'])
@app.route('/api/events/<event_id>', methods=['GET', 'POST'])
@login_required
def api_events(event_id=None):

    if request.method == 'GET':
        if event_id is not None:
            event_id = f'ID={id}'
        
        data = zip_table(table_name='events', where_clause=event_id)
        return jsonify(data)

    if request.method == 'POST':
        
        # Validate the post request
        if 'action' not in request.form:
            return jsonify({ 'error': 'Ahhh I dont know what to do, please provide an action'})

        action = request.form['action']

        pattern = r'\[(\d+)\]\[([a-zA-Z_]+)\]'
        data = {}
        id = 0
        query = ""

        for key in request.form.keys():
            print(f"Key: {key}", file=sys.stderr)
            matches = re.search(pattern, key)
            if matches:
                id = int(matches.group(1))
                field_key = matches.group(2)
                data[field_key] = request.form[key]

        # Handle Editing an existing record
        if action.lower() == 'edit':

            set_elem = []
            for col in data.keys():
                set_elem.append(f" {col}='{data[col]}'")

            query = f"UPDATE events SET {', '.join(set_elem)} WHERE ID={id}"

            print(f"Query: {query}", file=sys.stderr)
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
            
            new_data = zip_table(table_name='events', where_clause=f'ID={id}')
            jnew_data = jsonify(new_data)
            send_sio_msg('edit_events', jnew_data)
            return jnew_data

        # Handle Creating a new record
        if action.lower() == 'create':
            col_elem = data.keys()
            val_elem = []
            for col in col_elem:
                val_elem.append(f"'{data[col]}'")

            query = f"INSERT INTO EVENTS ( {', '.join(col_elem) }) VALUES ({ ', '.join(val_elem) })"
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                id = cursor.lastrowid
                conn.commit()
            new_data = zip_table(table_name='events', where_clause=f'ID={id}')
            jnew_data = jsonify(new_data)
            send_sio_msg('new_event', jnew_data)
            return jnew_data

        # Handle Remove
        if action.lower() == 'remove':
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM events WHERE id={id}")
                conn.commit()
            
            new_data = zip_table(table_name='events', where_clause=f'ID={id}')
            jnew_data = jsonify(new_data)
            send_sio_msg('remove_events', jnew_data)
            return jnew_data



    return jsonify("Oh no, you should never be here...")


# *====================================================================*
#         API
# *====================================================================*
@app.route('/api/observations', methods=['GET', 'POST'])
@app.route('/api/observations/', methods=['GET', 'POST'])
@app.route('/api/observations/<event_id>', methods=['GET', 'POST'])
@login_required
def api_observations(observation_id=None):

    if request.method == 'GET':
        if observation_id is not None:
            observation_id = f'ID={id}'
        
        data = zip_table(table_name='observations', where_clause=observation_id)
        return jsonify(data)

    if request.method == 'POST':
        
        # Validate the post request
        if 'action' not in request.form:
            return jsonify({ 'error': 'Ahhh I dont know what to do, please provide an action'})

        action = request.form['action']

        pattern = r'\[(\d+)\]\[([a-zA-Z_]+)\]'
        data = {}
        id = 0
        query = ""

        for key in request.form.keys():
            print(f"Key: {key}", file=sys.stderr)
            matches = re.search(pattern, key)
            if matches:
                id = int(matches.group(1))
                field_key = matches.group(2)
                data[field_key] = request.form[key]

        # Handle Editing an existing record
        if action.lower() == 'edit':

            set_elem = []
            for col in data.keys():
                set_elem.append(f" {col}='{data[col]}'")

            query = f"UPDATE observations SET {', '.join(set_elem)} WHERE ID={id}"

            print(f"Query: {query}", file=sys.stderr)
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
            
            new_data = zip_table(table_name='observations', where_clause=f'ID={id}')
            jnew_data = jsonify(new_data)
            send_sio_msg('edit_observations', jnew_data)
            return jnew_data

        # Handle Creating a new record
        if action.lower() == 'create':
            col_elem = data.keys()
            val_elem = []
            for col in col_elem:
                val_elem.append(f"'{data[col]}'")

            query = f"INSERT INTO observations ( {', '.join(col_elem) }) VALUES ({ ', '.join(val_elem) })"
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                id = cursor.lastrowid
                conn.commit()
            new_data = zip_table(table_name='observations', where_clause=f'ID={id}')
            jnew_data = jsonify(new_data)
            send_sio_msg('new_observation', jnew_data)
            return jnew_data

        # Handle Remove
        if action.lower() == 'remove':
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM observations WHERE id={id}")
                conn.commit()
            
            new_data = zip_table(table_name='observations', where_clause=f'ID={id}')
            jnew_data = jsonify(new_data)
            send_sio_msg('remove_observations', jnew_data)
            return jnew_data



    return jsonify("Oh no, you should never be here...")


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
    create_database()
    socketio.run(app, debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)

    
