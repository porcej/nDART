from extensions import db
from uuid import uuid4
from datetime import datetime, UTC
from models.user import user_roles  # Import the association table

class Role(db.Model):
    """Role model for user permissions."""
    __tablename__ = 'roles'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    active = db.Column(db.Boolean, default=True)

    # The 'users' backref will be created by the User.roles relationship

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Role {self.name}>' 