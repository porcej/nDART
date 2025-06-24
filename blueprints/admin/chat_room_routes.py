from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db
from models import User, Role, ChatRoom, ChatMessage, StationStatus, Assignment, ObservationsCategory
from datetime import datetime, UTC
from uuid import uuid4
from . import admin_bp
from .utils import admin_required
import pandas as pd
from io import BytesIO

# --------------------
# Chat Room Management
# --------------------
@admin_bp.route('/chat-rooms', methods=['GET'])
@login_required
@admin_required
def chat_rooms():
    """Display all chat rooms."""
    chat_rooms = ChatRoom.query.all()
    return render_template('admin/chat_rooms.html', chat_rooms=chat_rooms, username=current_user.name, is_admin=True, is_manager=current_user.is_manager)

@admin_bp.route('/chat-rooms/<id>', methods=['GET'])
@login_required
@admin_required
def get_chat_room(id):
    """Get a single chat room by UUID."""
    chat_room = ChatRoom.query.get_or_404(id)
    return jsonify(chat_room.to_dict())

@admin_bp.route('/chat-rooms', methods=['POST'])
@login_required
@admin_required
def create_chat_room():
    """Create a new chat room."""
    try:
        data = request.get_json()
        
        # Check if name already exists
        if ChatRoom.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Chat room name already exists'}), 400
        
        is_default = data.get('default', False)

        if is_default:
            # Set all other default rooms to non-default
            ChatRoom.query.filter_by(default=True).update({ChatRoom.default: False})

        # Create new chat room
        chat_room = ChatRoom(
            name=data['name'],
            description=data.get('description', ''),
            default=is_default,
            enabled=data.get('enabled', True)
        )
        
        db.session.add(chat_room)
        db.session.commit()
        
        return jsonify(chat_room.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/chat-rooms/<id>', methods=['PUT'])
@login_required
@admin_required
def update_chat_room(id):
    """Update an existing chat room."""
    try:
        chat_room = ChatRoom.query.get_or_404(id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data and data['name'] != chat_room.name:
            # Check if name is already taken
            existing = ChatRoom.query.filter_by(name=data['name']).first()
            if existing and existing.id != chat_room.id:
                return jsonify({'error': 'Chat room name already exists'}), 400
            chat_room.name = data['name']
            
        if 'description' in data:
            chat_room.description = data['description']

        if 'default' in data:
            chat_room.default = data['default']
            
        if 'enabled' in data:
            chat_room.enabled = data['enabled']
            
        db.session.commit()
        
        return jsonify(chat_room.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/chat-rooms/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_chat_room(id):
    """Delete a chat room."""
    try:
        chat_room = ChatRoom.query.get_or_404(id)
        db.session.delete(chat_room)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chat room deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/chat-rooms/<id>/clear-messages', methods=['DELETE'])
@login_required
@admin_required
def clear_chat_room_messages(id):
    """Clear all messages in a chat room."""
    try:
        chat_room = ChatRoom.query.get_or_404(id)
        
        # Delete all messages associated with this chat room
        ChatMessage.query.filter_by(room_id=id).delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Messages cleared successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400