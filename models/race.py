from datetime import datetime, UTC
from uuid import uuid4

from extensions import db

RACE_STATUS_ACTIVE = 'active'
RACE_STATUS_ARCHIVED = 'archived'


class Race(db.Model):
    """A discrete race-day occurrence that scopes operational data."""
    __tablename__ = 'races'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(200), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=RACE_STATUS_ACTIVE)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    events = db.relationship('Event', back_populates='race', lazy='dynamic')
    observations = db.relationship('Observation', back_populates='race', lazy='dynamic')
    status_reports = db.relationship('StatusReport', back_populates='race', lazy='dynamic')
    staffer_volunteers = db.relationship('StafferAROVolunteer', back_populates='race', lazy='dynamic')
    chat_rooms = db.relationship('ChatRoom', back_populates='race', lazy='dynamic')

    def __repr__(self):
        return f'<Race {self.name} ({self.status})>'

    @property
    def is_archived(self):
        return self.status == RACE_STATUS_ARCHIVED

    @property
    def is_writable(self):
        return self.status == RACE_STATUS_ACTIVE

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'ends_at': self.ends_at.isoformat() if self.ends_at else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_archived': self.is_archived,
            'is_writable': self.is_writable,
        }
