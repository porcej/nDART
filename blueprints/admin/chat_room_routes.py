from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import ChatRoom, ChatMessage
from . import admin_bp
from .utils import admin_required
from blueprints.race_context import (
    apply_race_filter,
    require_writable_race,
    require_writable_race_for_row,
)

# --------------------
# Chat Room Management
# --------------------
@admin_bp.route('/chat-rooms', methods=['GET'])
@login_required
@admin_required
def chat_rooms():
    """Display chat rooms for the current race."""
    chat_rooms = apply_race_filter(ChatRoom.query, ChatRoom).all()
    return render_template(
        'admin/chat_rooms.html',
        chat_rooms=chat_rooms,
        username=current_user.name,
        is_admin=True,
        is_manager=current_user.is_manager,
    )

@admin_bp.route('/chat-rooms/<id>', methods=['GET'])
@login_required
@admin_required
def get_chat_room(id):
    """Get a single chat room by UUID."""
    chat_room = apply_race_filter(ChatRoom.query.filter_by(id=id), ChatRoom).first_or_404()
    return jsonify(chat_room.to_dict())

@admin_bp.route('/chat-rooms', methods=['POST'])
@login_required
@admin_required
def create_chat_room():
    """Create a new chat room for the current race."""
    try:
        race, err = require_writable_race()
        if err is not None:
            return err

        data = request.get_json()
        
        if apply_race_filter(ChatRoom.query.filter_by(name=data['name']), ChatRoom).first():
            return jsonify({'error': 'Chat room name already exists'}), 400
        
        is_default = data.get('default', False)

        if is_default:
            apply_race_filter(ChatRoom.query.filter_by(default=True), ChatRoom).update(
                {ChatRoom.default: False}, synchronize_session=False
            )

        chat_room = ChatRoom(
            name=data['name'],
            description=data.get('description', ''),
            default=is_default,
            enabled=data.get('enabled', True),
            race_id=race.id,
        )
        
        db.session.add(chat_room)
        db.session.commit()
        
        return jsonify({
            'success': 'Chat room created successfully.',
            'data': chat_room.to_dict(),
        }), 201
        
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to create chat room.'}), 400

@admin_bp.route('/chat-rooms/<id>', methods=['PUT'])
@login_required
@admin_required
def update_chat_room(id):
    """Update an existing chat room."""
    try:
        chat_room = apply_race_filter(ChatRoom.query.filter_by(id=id), ChatRoom).first_or_404()
        _race, err = require_writable_race_for_row(chat_room)
        if err is not None:
            return err

        data = request.get_json()
        
        if 'name' in data and data['name'] != chat_room.name:
            existing = apply_race_filter(
                ChatRoom.query.filter_by(name=data['name']), ChatRoom
            ).first()
            if existing and existing.id != chat_room.id:
                return jsonify({'error': 'Chat room name already exists'}), 400
            chat_room.name = data['name']
            
        if 'description' in data:
            chat_room.description = data['description']

        if 'default' in data:
            if data['default']:
                apply_race_filter(ChatRoom.query.filter_by(default=True), ChatRoom).update(
                    {ChatRoom.default: False}, synchronize_session=False
                )
            chat_room.default = data['default']
            
        if 'enabled' in data:
            chat_room.enabled = data['enabled']
            
        db.session.commit()
        
        return jsonify({
            'success': 'Chat room updated successfully.',
            'data': chat_room.to_dict(),
        })
        
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to update chat room.'}), 400

@admin_bp.route('/chat-rooms/<id>', methods=['DELETE'])
@login_required
@admin_required
def delete_chat_room(id):
    """Delete a chat room."""
    try:
        chat_room = apply_race_filter(ChatRoom.query.filter_by(id=id), ChatRoom).first_or_404()
        _race, err = require_writable_race_for_row(chat_room)
        if err is not None:
            return err

        db.session.delete(chat_room)
        db.session.commit()
        
        return jsonify({'success': 'Chat room deleted successfully.'})
        
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete chat room.'}), 400

@admin_bp.route('/chat-rooms/<id>/clear-messages', methods=['DELETE'])
@login_required
@admin_required
def clear_chat_room_messages(id):
    """Clear all messages in a chat room."""
    try:
        chat_room = apply_race_filter(ChatRoom.query.filter_by(id=id), ChatRoom).first_or_404()
        _race, err = require_writable_race_for_row(chat_room)
        if err is not None:
            return err
        
        ChatMessage.query.filter_by(room_id=id).delete()
        db.session.commit()
        
        return jsonify({'success': 'Messages cleared successfully.'})
        
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to clear chat room messages.'}), 400
