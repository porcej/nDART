from extensions import db
from uuid import uuid4

class Assignment(db.Model):
    """Model for assignments"""
    __tablename__ = 'assignments'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    short_code = db.Column(db.String(20), nullable=True)
    description = db.Column(db.String(200), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    enabled = db.Column(db.Boolean, default=True)

    # Relationships
    events = db.relationship('Event', lazy=True, 
                           foreign_keys='Event.reporter_id',
                           back_populates='reporter',
                           cascade='all')
    observations = db.relationship('Observation', lazy=True, 
                           foreign_keys='Observation.reporter_id',
                           back_populates='reporter',
                           cascade='all')
    status_reports = db.relationship('StatusReport', lazy=True, 
                           foreign_keys='StatusReport.reporter_id',
                           back_populates='reporter',
                           cascade='all')

    def __repr__(self):
        return f"<Assignment {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'short_code': self.short_code,
            'description': self.description,
            'sort_order': self.sort_order,
            'enabled': self.enabled,
        }
    
    def get_display_name(self):
        """Get the display name (short_code if available, otherwise name)"""
        return self.short_code if self.short_code else self.name
    
    def to_form_options(self):
        return {
            'label': self.name,
            'value': self.id,
            'sort_order': self.sort_order
        }
    
    def get_assignment_events(self):
        return Event.query.filter_by(reporter_id=self.id).all()
    
    def get_assignment_observations(self):
        return Observation.query.filter_by(reporter_id=self.id).all()
    
    def get_assignment_status_reports(self):
        return StatusReport.query.filter_by(reporter_id=self.id).all()