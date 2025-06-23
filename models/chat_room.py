from datetime import datetime, UTC
from extensions import db
from uuid import uuid4

class ChatRoom(db.Model):
    """Model for chat rooms."""
    __tablename__ = 'chat_rooms'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    default = db.Column(db.Boolean, default=False, nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    max_participants = db.Column(db.Integer, default=100)
    is_private = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(255), nullable=True)
    moderators = db.Column(db.JSON, default=list)  # Store moderator UUIDs
    
    # Add these relationships after the columns
    messages = db.relationship('ChatMessage', lazy=True, 
                               foreign_keys='ChatMessage.room_id',
                               back_populates='room',
                               cascade='all')

    def __repr__(self):
        return f'<ChatRoom {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'default': self.default
        }