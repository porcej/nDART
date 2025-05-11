from extensions import db
from uuid import uuid4

class Observation(db.Model):
    """Model for observations"""
    __tablename__ = 'observations'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    time = db.Column(db.DateTime, nullable=True)
    bib = db.Column(db.String(10), nullable=True)
    reporter = db.Column(db.String(100), nullable=True)
    location_id = db.Column(db.String(36), db.ForeignKey('location.id'), nullable=True)
    category_id = db.Column(db.String(36), db.ForeignKey('observations_category.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    location = db.relationship('Location', backref=db.backref('observations', lazy=True))
    category = db.relationship('ObservationsCategory', backref=db.backref('observations', lazy=True))

    def __repr__(self):
        return f"<Observation {self.id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time,
            'bib': self.bib,
            'reporter': self.reporter,
            'location': self.location.to_dict(),
            'category': self.category.to_dict(),
            'notes': self.notes
        }