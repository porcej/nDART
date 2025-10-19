#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SocketIO API Routes for nDART Application

This module contains SocketIO event handlers for the /api namespace.
"""

from flask import Blueprint
from flask_socketio import emit
from extensions import socketio

# Create the SocketIO API blueprint
socketio_api_bp = Blueprint('socketio_api', __name__)


@socketio.on('connect', namespace="/api")
def test_connect():
    """Handler for a message received over 'connect' channel."""
    emit('after connect', {'data': 'Lets dance'})


def send_sio_msg(msg_type, msg, room=None):
    """Helper function to send SocketIO messages."""
    broadcast = room is None
    socketio.emit(msg_type, namespace='/api')
