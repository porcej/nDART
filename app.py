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

    # Encounters Table - Holds a list of all encounters
    cursor.execute('''CREATE TABLE IF NOT EXISTS encounters (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      aid_station TEXT,
                      bib TEXT,
                      first_name TEXT,
                      last_name TEXT,
                      age INTEGER,
                      sex TEXT,
                      participant INTEGER,
                      active_duty INTEGER,
                      time_in TEXT,
                      time_out TEXT,
                      presentation TEXT,
                      vitals TEXT,
                      iv TEXT,
                      iv_fluid_count INTEGER,
                      oral_fluid INTEGER,
                      food INTEGER,
                      na TEXT,
                      kplus TEXT,
                      cl TEXT,
                      tco TEXT,
                      bun TEXT,
                      cr TEXT,
                      glu TEXT,
                      treatments TEXT,
                      disposition TEXT,
                      hospital TEXT,
                      notes TEXT
                   )''')

    # Vitals Table - Holds a List of all Vitasl
    cursor.execute('''CREATE TABLE IF NOT EXISTS vitals (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      encounter_id INTEGER,
                      vital_time TEXT,
                      temp TEXT,
                      resp TEXT,
                      pulse TEXT,
                      bp TEXT,
                      notes TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS persons (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      bib TEXT,
                      first_name TEXT,
                      last_name TEXT,
                      age INTEGER,
                      sex TEXT,
                      participant INTEGER,
                      active_duty INTEGER
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS presentation (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      code TEXT,
                      description TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS disposition (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      code TEXT,
                      description TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      password TEXT NOT NULL,
                      role TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS aid_stations (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL
                   )''')



    print("Database created!", file=sys.stderr)
    conn.commit()
    conn.close()


# Function to export data as a zipped dict
def zip_encounters(id=None, aid_station=None):
    where_clause = None
    if id is not None or aid_station is not None:
        if id is not None:
            where_clause = f'ID={id}'
        if aid_station is not None:
            where_clause = f"aid_station='{aid_station}'"

    data = zip_table(table_name='encounters', where_clause=where_clause)
    return data


# Function to export data as a zipped dict
def zip_vitals(encounter_id=None, id=None):
    where_clause = None
    if encounter_id is not None and id is not None:
        where_clause = f'ENCOUNTER_ID={encounter_id} AND ID={id}'
    elif encounter_id is None and id is None:
        return {'data': []}
    else:
        if encounter_id is not None:
            where_clause = f'ENCOUNTER_ID={encounter_id}'
        if id is not None:
            where_clause = f'id={id}'

    data = zip_table(table_name='vitals', where_clause=where_clause)
    return data


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
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('app_index'))
    if request.method == 'POST':
        if 'remove-people' in request.form:
            remove_all_rows('persons')
            return f'All removed all runners.'
        elif 'remove-encounters' in request.form:
            remove_all_rows('encounters')
            send_sio_msg('remove_encounter', 'File Uploaded')
            return f'All removed all encounters.'
        elif 'export-people' in request.form:
            return export_to_xlsx('persons')
        elif 'export-encounters' in request.form:
            return export_to_xlsx('encounters')
        elif 'participants-file' in request.files:
            file = request.files['participants-file']
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
                df['participant'] = 1
                save_to_database(df, 'persons')
                return 'File uploaded and data loaded into database successfully!'
            else:
                return 'Only xlsx files are allowed!'
        elif 'encounters-file' in request.files:
            file = request.files['encounters-file']
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
                save_to_database(df, 'encounters')
                send_sio_msg('new_encounter', 'File Uploaded')
                return 'File uploaded and data loaded into database successfully!'
            else:
                return 'Only xlsx files are allowed!'
        else:
            return 'I am not a teapot.'

    return render_template('admin.html')

# Save DataFrame to SQLite database
def save_to_database(df, table):
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
        df.to_sql(table, conn, if_exists='replace', index=False)

# Remove all rows from the table
def remove_all_rows(table):
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
        conn.execute(f'DELETE FROM {table}')

# Export SQLite table to xlsx file
def export_to_xlsx(table):
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
        df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name=table)
    writer.close()
    output.seek(0)
    return send_file(output, download_name=f'{table}.xlsx', as_attachment=True)


# *====================================================================*
#         API
# *====================================================================*
@app.route('/api/participants/', methods=['GET'])
@login_required
def api_participants():
    data = zip_table("persons")
    return jsonify(data)


@app.route('/api/encounters', methods=['GET', 'POST'])
@app.route('/api/encounters/<aid_station>', methods=['GET', 'POST'])
@login_required
def api_encounters(aid_station=None):
    if aid_station is not None:
        aid_station = aid_station.replace("_", " ")
        aid_station = aid_station.replace("--", "/")

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

            query = f"UPDATE encounters SET {', '.join(set_elem)} WHERE ID={id}"

            print(f"Query: {query}", file=sys.stderr)
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
            
            new_data = zip_encounters(id=id)
            jnew_data = jsonify(new_data)
            send_sio_msg('edit_encounter', jnew_data)
            return jnew_data

        # Handle Creating a new record
        if action.lower() == 'create':
            col_elem = data.keys()
            val_elem = []
            for col in col_elem:
                val_elem.append(f"'{data[col]}'")

            query = f"INSERT INTO encounters ( {', '.join(col_elem) }) VALUES ({ ', '.join(val_elem) })"
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                id = cursor.lastrowid
                conn.commit()
            new_data = zip_encounters(id=id)
            jnew_data = jsonify(new_data)
            send_sio_msg('new_encounter', jnew_data)
            return jnew_data

        # Handle Remove
        if action.lower() == 'remove':
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM encounters WHERE id={id}")
                conn.commit()
            
            new_data = zip_encounters(id=id)
            jnew_data = jsonify(new_data)
            send_sio_msg('remove_encounter', jnew_data)
            return jnew_data

    # Handle Get Request
    if request.method == "GET":
        with sqlite3.connect(Config.DATABASE_PATH) as conn:
            data = zip_encounters(aid_station=aid_station)
        return jsonify(data)

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

    
