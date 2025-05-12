from extensions import db
from uuid import uuid4

class Assignment(db.Model):
    """Model for assignments"""
    __tablename__ = 'assignments'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
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

    def __repr__(self):
        return f"<Assignment {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
        }