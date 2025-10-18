from datetime import datetime, UTC
from flask import render_template, request, jsonify, url_for, current_app
from flask_login import current_user, login_required
from flask_socketio import emit, join_room
from werkzeug.utils import secure_filename
import os
from functools import wraps
import bleach
import logging

from extensions import db, socketio
from models import ChatMessage, ChatRoom, User
from . import chat_bp

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chat_bp.route('/')
@login_required
def chat():
    """Chat room. The user's name and room must be stored in
    the session."""

    chat_rooms = [room.to_dict() for room in ChatRoom.query.filter(ChatRoom.enabled == True).all()]
    return render_template('chat/index.html', chat_rooms=chat_rooms)

# Socket.IO event handlers
@socketio.on('join', namespace='/chat')
@login_required
def handle_join(data):
    room_id = data['room_id']
    join_room(room_id)
    previous_messages = ChatMessage.query.filter_by(room_id=room_id, deleted_flag=False).all()
    emit('previous_messages', [msg.to_dict() for msg in previous_messages], room=request.sid)

@socketio.on('send_message', namespace='/chat')
@login_required
def handle_send_message(data):
    logger.info(f"Received send_message: {data}")
    room_id = data['room_id']
    # nick_name = data['nick_name']
    sender = current_user.name
    content = data['message']
    created_at = datetime.now(UTC)

    message = ChatMessage(
        room_id=room_id,
        # nick_name=nick_name,
        sender=sender,
        content=content,
        created_at=created_at
    )
    db.session.add(message)
    db.session.commit()

    message_dict = message.to_dict()
    logger.info(f"Emitting receive_message to room {room_id}: {message_dict}")
    emit('receive_message', message_dict, room=room_id)

@socketio.on('leave', namespace='/chat')
@login_required
def handle_leave(data):
    room_id = data['room_id']
    from flask_socketio import leave_room
    leave_room(room_id)
    emit('status', {'msg': f'{current_user.name} has left the room.'}, room=room_id)

@socketio.on('typing', namespace='/chat')
@login_required
def handle_typing(data):
    room_id = data['room_id']
    emit('user_typing', {'user': current_user.name}, room=room_id, include_self=False)

@socketio.on('stop_typing', namespace='/chat')
@login_required
def handle_stop_typing(data):
    room_id = data['room_id']
    emit('user_stop_typing', {'user': current_user.name}, room=room_id, include_self=False)

@chat_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({
            'success': True,
            'file_url': url_for('static', filename=f'uploads/{filename}')
        })
    
    return jsonify({'success': False, 'error': 'File type not allowed'})

@chat_bp.route('/message/<message_id>', methods=['PUT'])
@login_required
def edit_message(message_id):
    message = ChatMessage.query.get_or_404(message_id)
    if message.sender != request.sid:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.get_json()
    message.content = data['content']
    message.edited = True
    message.edited_at = datetime.now(UTC)
    db.session.commit()
    
    return jsonify({'success': True})

def rate_limit_messages():
    """Rate limiting decorator for messages"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = f"rate_limit:{current_user.id}"
            # if redis_client.get(key):
            #     return jsonify({'success': False, 'error': 'Rate limit exceeded'})
            # redis_client.setex(key, 1, 1)  # 1 message per second
            return f(*args, **kwargs)
        return wrapped
    return decorator

def sanitize_message(content):
    """Sanitize message content to prevent XSS"""
    return bleach.clean(content, strip=True)

@chat_bp.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Chat error: {str(error)}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'An error occurred',
        'details': str(error) if current_app.debug else None
    }), 500