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
Config.USER_ACCOUNTS =  {k.lower(): v for k, v in Config.USER_ACCOUNTS.items()}

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

    cursor.execute('''CREATE TABLE IF NOT EXISTS observations_categories (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      value TEXT NOT NULL UNIQUE,
                      display TEXT,
                      active INTEGER NOT NULL DEFAULT 1
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      value TEXT NOT NULL UNIQUE,
                      display TEXT,
                      active INTEGER NOT NULL DEFAULT 1
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS agencies (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      value TEXT NOT NULL UNIQUE,
                      display TEXT,
                      active INTEGER NOT NULL DEFAULT 1
                   )''')

    # Add Categories for the Observations
    try:
        cursor.execute('''INSERT INTO agencies(value, display, active)
                    VALUES
                    ('Arl Fire', 'Arl Fire', 1),
                    ('DC FEMS', 'DC FEMS', 1),
                    ('Law', 'Law', 1)
                ''')
    except Exception as e:
        pass # Its okay, we have already added these values

    # Add Categories for the Observations
    try:
        cursor.execute('''INSERT INTO observations_categories(value, display, active)
                    VALUES
                    ('Male', 'Male', 1),
                    ('Female', 'Female', 1),
                    ('Wheelchair', 'Wheelchair', 1)
                ''')
    except Exception as e:
        pass # Its okay, we have already added these values

    # Add Locations
    try:
        cursor.execute('''INSERT INTO locations(value, display, active)
                    VALUES
                    ('MMO', 'MMO', 1),
                    ('MM1', 'MM1', 1),
                    ('MM2', 'MM2', 1),
                    ('WP1', 'WP1', 1),
                    ('MM2.7', 'MM2.7', 1),
                    ('MM3.6', 'MM3.6', 1),
                    ('MM4', 'MM4', 1),
                    ('MM4.5', 'MM4.5', 1),
                    ('MM50.1', 'MM50.1', 1),
                    ('MM50.2', 'MM50.2', 1),
                    ('AS50', 'AS50', 1),
                    ('MM50.3', 'MM50.3', 1),
                    ('AS1', 'AS1', 1),
                    ('WP2', 'WP2', 1),
                    ('MM5', 'MM5', 1),
                    ('MM5.5', 'MM5.5', 1),
                    ('MM6', 'MM6', 1),
                    ('WP3', 'WP3', 1),
                    ('AS2/3', 'AS2/3', 1),
                    ('MM7', 'MM7', 1),
                    ('MM7.5', 'MM7.5', 1),
                    ('MM8', 'MM8', 1),
                    ('MM9', 'MM9', 1),
                    ('MM10', 'MM10', 1),
                    ('WP5/7', 'WP5/7', 1),
                    ('AS4/6', 'AS4/6', 1),
                    ('MM11', 'MM11', 1),
                    ('MM11.5', 'MM11.5', 1),
                    ('MM12', 'MM12', 1),
                    ('MM12.5', 'MM12.5', 1),
                    ('MM13', 'MM13', 1),
                    ('MM13.5', 'MM13.5', 1),
                    ('WP6', 'WP6', 1),
                    ('MM14', 'MM14', 1),
                    ('MM14.5', 'MM14.5', 1),
                    ('MM15', 'MM15', 1),
                    ('MM15.5', 'MM15.5', 1),
                    ('MM16', 'MM16', 1),
                    ('MM16.5', 'MM16.5', 1),
                    ('MM17', 'MM17', 1),
                    ('AS7', 'AS7', 1),
                    ('MM17.5', 'MM17.5', 1),
                    ('MM18', 'MM18', 1),
                    ('MM18.5', 'MM18.5', 1),
                    ('FS1', 'FS1', 1),
                    ('MM19', 'MM19', 1),
                    ('AS8', 'AS8', 1),
                    ('MM19.5', 'MM19.5', 1),
                    ('MM20', 'MM20', 1),
                    ('MM20.5', 'MM20.5', 1),
                    ('MM21', 'MM21', 1),
                    ('MM21.5', 'MM21.5', 1),
                    ('AS9', 'AS9', 1),
                    ('WP10', 'WP10', 1),
                    ('MM22', 'MM22', 1),
                    ('MM22.5', 'MM22.5', 1),
                    ('MM22.7', 'MM22.7', 1),
                    ('MM23', 'MM23', 1),
                    ('MM23.5', 'MM23.5', 1),
                    ('FS2', 'FS2', 1),
                    ('WP11', 'WP11', 1),
                    ('AS10', 'AS10', 1),
                    ('MM24', 'MM24', 1),
                    ('MM24.5', 'MM24.5', 1),
                    ('WP12', 'WP12', 1),
                    ('MM25', 'MM25', 1),
                    ('MM25.5', 'MM25.5', 1),
                    ('MM26', 'MM26', 1)
                ''')
    except Exception as e:
        pass # Its okay, we have already added these values


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

    if username is not None:
        username = username.lower()

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
    return redirect(url_for('events'))

@app.route('/events')
@login_required
def events():
    # conn = db_connect()
    # cursor = conn.cursor()
    # conn.close()
    return render_template("events.html", active_page='events', is_admin=current_user.is_admin)

@app.route('/observations')
@login_required
def observations():
    # conn = db_connect()
    # cursor = conn.cursor()
    # conn.close()
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

# Remove all rows from the table
def remove_all_rows(table):
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table}')
        conn.commit()
    

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

    
