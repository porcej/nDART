from extensions import db
from uuid import uuid4

class Observation(db.Model):
    """Model for observations"""
    __tablename__ = 'observations'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    time = db.Column(db.DateTime, nullable=True)
    bib = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    reporter_id = db.Column(db.String(36), db.ForeignKey('assignments.id'), nullable=True)
    category_id = db.Column(db.String(36), db.ForeignKey('observations_categories.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    delete_flag = db.Column(db.Boolean, default=False)

    # Add these relationships after the columns
    category = db.relationship('ObservationsCategory', foreign_keys=[category_id], back_populates='observations')
    reporter = db.relationship('Assignment', foreign_keys=[reporter_id], back_populates='observations')

    def __repr__(self):
        return f"<Observation {self.id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time.strftime("%H:%M") if self.time else None,
            'bib': self.bib,
            'reporter': self.reporter_id,
            'location': self.location,
            'category': self.category_id,
            'notes': self.notes,
            'delete_flag': self.delete_flag
        }