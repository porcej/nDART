from datetime import datetime, UTC
from extensions import db
from uuid import uuid4

class ChatMessage(db.Model):
    """Model for chat messages."""
    __tablename__ = 'chat_messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    sender = db.Column(db.String(80), nullable=False)
    nick_name = db.Column(db.String(80), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    parent_message_id = db.Column(db.String(36), db.ForeignKey('chat_messages.id'), nullable=True)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, syzstem
    status = db.Column(db.String(20), default='sent')  # sent, delivered, read
    deleted_flag = db.Column(db.Boolean, default=False)

    # Add these relationships after the columns
    room = db.relationship('ChatRoom', foreign_keys=[room_id], back_populates='messages')

    def to_dict(self):
        """Convert chat message to dictionary."""
        return {
            'id': self.id,
            'room_id': self.room_id,
            'sender': self.sender,
            'nick_name': self.nick_name,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<ChatMessage {self.id}>' 