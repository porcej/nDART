from extensions import db
from uuid import uuid4

class Agency(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(200), nullable=True)
    enabled = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Agency {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'enabled': self.enabled
        }