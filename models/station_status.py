from extensions import db
from uuid import uuid4

class StationStatus(db.Model):
    """Model for station statuses"""
    __tablename__ = 'station_statuses'

    # Columns   
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(50), nullable=True)  # Bootstrap color class
    icon = db.Column(db.String(50), nullable=True)  # Icon class or name
    description = db.Column(db.Text, nullable=True)
    enabled = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    # Relationships
    status_reports = db.relationship('StatusReport', lazy=True, 
                           foreign_keys='StatusReport.status_id',
                           back_populates='status',
                           cascade='all')

    def __repr__(self):
        return f"<StationStatus {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'description': self.description,
            'sort_order': self.sort_order,
            'enabled': self.enabled,
        }
    
    def to_form_options(self):
        return {
            'label': self.name,
            'value': self.id,
            'sort_order': self.sort_order
        }