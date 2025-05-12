from datetime import datetime
from extensions import socketio

def send_event_notification(event_type, data, room=None):
    """
    Send Socket.IO notifications for events.
    
    Args:
        event_type (str): Type of event ('new_event', 'edit_event', 'remove_event')
        data (dict): Data to send with the event
        room (str, optional): Room to send the event to. Defaults to None (broadcast).
    """
    broadcast = room is None
    socketio.emit(event_type, data, namespace='/api', room=room) 

def send_observation_notification(event_type, data, room=None):
    """
    Send Socket.IO notifications for observations.
    
    Args:
        event_type (str): Type of event ('new_observation', 'edit_observation', 'remove_observation')
        data (dict): Data to send with the event
        room (str, optional): Room to send the event to. Defaults to None (broadcast).
    """
    broadcast = room is None
    socketio.emit(event_type, data, namespace='/api', room=room) 

def send_update_notification(update_type,room=None):
    """
    Send Socket.IO notifications for agencies.
    
    Args:
        update_type (str): Type of update ('agency_update', 'assignment_update', 'observation_category_update')
        room (str, optional): Room to send the notification to. Defaults to None (broadcast).
    """
    broadcast = room is None
    socketio.emit(update_type, {}, namespace='/api', room=room)

def send_agency_notification(room=None):
    """
    Send Socket.IO notifications for agencies.
    
    Args:
        room (str, optional): Room to send the notification to. Defaults to None (broadcast).
    """
    broadcast = room is None
    socketio.emit("agency_update", {}, namespace='/api', room=room) 


# API Utilities
def handle_date_fields(data):
    """
    Convert time fields to datetime objects.
    """

    time_fields = ['time_in', 'agency_notified', 'agency_arrival', 'resolved', 'time']
    new_data = {}
    for key, value in data.items():
        # if (value is not None and value != ''):
        if key in time_fields:
            if (value is not None and value != ''):
                new_data[key] = datetime.strptime(value, "%H:%M")
            else:
                new_data[key] = None
        else:
            new_data[key] = value
    return new_data
