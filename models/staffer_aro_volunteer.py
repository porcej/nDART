from extensions import db
from uuid import uuid4

class StafferAROVolunteer(db.Model):
    """Model for mapping nDART assignments to staffer ARO volunteer information"""
    __tablename__ = 'staffer_aro_volunteers'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    assignment_id = db.Column(db.String(36), db.ForeignKey('assignments.id'), nullable=True)
    staffer_assignment = db.Column(db.String(200), nullable=True)  # Original assignment name from staffer
    short_code = db.Column(db.String(20), nullable=True)
    callsign = db.Column(db.String(50), nullable=False)  # Callsign is unique identifier
    email = db.Column(db.String(120), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True)  # Current status from staffer
    status_timestamp = db.Column(db.DateTime, nullable=True)  # When status was last updated
    race_id = db.Column(db.String(36), db.ForeignKey('races.id'), nullable=False, index=True)
    
    __table_args__ = (
        db.UniqueConstraint('race_id', 'callsign', name='uq_staffer_aro_volunteers_race_callsign'),
    )
    
    # Relationships
    assignment = db.relationship('Assignment', foreign_keys=[assignment_id], backref='staffer_volunteers')
    race = db.relationship('Race', foreign_keys=[race_id], back_populates='staffer_volunteers')
    
    def __repr__(self):
        return f"<StafferAROVolunteer {self.name} - {self.callsign}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'staffer_assignment': self.staffer_assignment,
            'short_code': self.short_code,
            'callsign': self.callsign,
            'email': self.email,
            'phone_number': self.phone_number,
            'name': self.name,
            'status': self.status,
            'status_timestamp': self.status_timestamp.isoformat() if self.status_timestamp else None,
            'race_id': self.race_id,
        }
    
    @staticmethod
    def get_by_assignment(assignment_id, race_id=None):
        """Get staffer volunteer info by assignment ID (optionally scoped to a race)."""
        q = StafferAROVolunteer.query.filter_by(assignment_id=assignment_id)
        if race_id is not None:
            q = q.filter_by(race_id=race_id)
        return q.first()
    
    @staticmethod
    def update_or_create_by_callsign(callsign, race_id, assignment_id=None, staffer_assignment=None, short_code=None, email=None, phone_number=None, name=None, status=None, status_timestamp=None):
        """Update existing or create new staffer volunteer mapping by callsign within a race."""
        volunteer = StafferAROVolunteer.query.filter_by(callsign=callsign, race_id=race_id).first()
        
        if volunteer:
            # Update existing
            if assignment_id is not None:
                volunteer.assignment_id = assignment_id
            if staffer_assignment is not None:
                volunteer.staffer_assignment = staffer_assignment
            if short_code is not None:
                volunteer.short_code = short_code
            if email is not None:
                volunteer.email = email
            if phone_number is not None:
                volunteer.phone_number = phone_number
            if name is not None:
                volunteer.name = name
            if status is not None:
                volunteer.status = status
            if status_timestamp is not None:
                volunteer.status_timestamp = status_timestamp
        else:
            # Create new
            volunteer = StafferAROVolunteer(
                assignment_id=assignment_id,
                staffer_assignment=staffer_assignment,
                short_code=short_code,
                callsign=callsign,
                email=email,
                phone_number=phone_number,
                name=name,
                status=status,
                status_timestamp=status_timestamp,
                race_id=race_id,
            )
            db.session.add(volunteer)
        
        db.session.commit()
        return volunteer
    
    @staticmethod
    def update_or_create(assignment_id, race_id, staffer_assignment=None, short_code=None, callsign=None, email=None, phone_number=None, name=None):
        """Update existing or create new staffer volunteer mapping - deprecated, use update_or_create_by_callsign"""
        return StafferAROVolunteer.update_or_create_by_callsign(
            callsign=callsign,
            race_id=race_id,
            assignment_id=assignment_id,
            staffer_assignment=staffer_assignment,
            short_code=short_code,
            email=email,
            phone_number=phone_number,
            name=name
        )

