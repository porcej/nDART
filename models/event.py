from extensions import db
from uuid import uuid4

class Event(db.Model):
    """Model for events"""
    __tablename__ = 'events'

    # Columns   
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    event_id = db.Column(db.Integer, autoincrement=True)
    time_in = db.Column(db.DateTime, nullable=True)
    bib = db.Column(db.String(10), nullable=True)
    reporter = db.Column(db.String(100), nullable=True)
    location_id = db.Column(db.String(36), db.ForeignKey('location.id'), nullable=True)
    agency_id = db.Column(db.String(36), db.ForeignKey('agency.id'), nullable=True)
    agency_notified = db.Column(db.DateTime, nullable=True)
    agency_arrival = db.Column(db.DateTime, nullable=True)
    resolved = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    delete_flag = db.Column(db.Boolean, default=False)
    
    # Relationships
    location = db.relationship('Location', backref=db.backref('events', lazy=True))
    agency = db.relationship('Agency', backref=db.backref('events', lazy=True))

    def __repr__(self):
        return f"<Event {self.id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'time_in': self.time_in,
            'bib': self.bib,
            'reporter': self.reporter,
            'location': self.location.to_dict(),
            'agency': self.agency.to_dict(),
            'agency_notified': self.agency_notified,
            'agency_arrival': self.agency_arrival,
            'resolved': self.resolved,
            'notes': self.notes,
            'delete_flag': self.delete_flag
        }
