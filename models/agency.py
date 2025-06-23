from extensions import db
from uuid import uuid4

class Agency(db.Model):
    """Model for agencies"""
    __tablename__ = 'agencies'

    # Columns   
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    enabled = db.Column(db.Boolean, default=True)

    # Relationships
    events = db.relationship('Event', lazy=True, 
                           foreign_keys='Event.agency_id',
                           back_populates='agency',
                           cascade='all')

    def __repr__(self):
        return f"<Agency {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'enabled': self.enabled
        }

    def to_form_options(self):
        return {
            'label': self.name,
            'value': self.id,
            'sort_order': self.sort_order
        }
    
    def get_agency_events(self):
        return Event.query.filter_by(agency_id=self.id).all()