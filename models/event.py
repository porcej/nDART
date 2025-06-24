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
    reporter_id = db.Column(db.String(36), db.ForeignKey('assignments.id'), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    agency_id = db.Column(db.String(36), db.ForeignKey('agencies.id'), nullable=True)
    agency_notified = db.Column(db.DateTime, nullable=True)
    agency_arrival = db.Column(db.DateTime, nullable=True)
    resolved = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    delete_flag = db.Column(db.Boolean, default=False)
    
    # Add these relationships after the columns
    reporter = db.relationship('Assignment', foreign_keys=[reporter_id], back_populates='events')
    agency = db.relationship('Agency', foreign_keys=[agency_id], back_populates='events')
    
    def __repr__(self):
        return f"<Event {self.id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'time_in': self.time_in.strftime("%H:%M") if self.time_in else None,
            'bib': self.bib,
            'reporter_id': self.reporter_id,
            'location': self.location,
            'agency_id': self.agency_id,
            'agency_notified': self.agency_notified.strftime("%H:%M") if self.agency_notified else None ,
            'agency_arrival': self.agency_arrival.strftime("%H:%M") if self.agency_arrival else None,
            'resolved': self.resolved.strftime("%H:%M") if self.resolved else None,
            'notes': self.notes,
            'delete_flag': self.delete_flag
        }
