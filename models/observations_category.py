from extensions import db
from uuid import uuid4

class ObservationsCategory(db.Model):
    """Model for observations categories"""
    __tablename__ = 'observations_categories'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    enabled = db.Column(db.Boolean, default=True)


    # Relationships
    observations = db.relationship('Observation', lazy=True, 
                           foreign_keys='Observation.category_id',
                           back_populates='category',
                           cascade='all')

    def __repr__(self):
        return f"<ObservationsCategory {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'observations': [observation.to_dict() for observation in self.observations],
            'sort_order': self.sort_order
        }
    
    def to_form_options(self):
        return {
            'label': self.name,
            'value': self.id,
            'sort_order': self.sort_order
        }