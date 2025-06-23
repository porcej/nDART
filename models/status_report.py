from extensions import db
from uuid import uuid4

class StatusReport(db.Model):
    """Model for status reports"""
    __tablename__ = 'status_reports'

    # Columns   
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    time = db.Column(db.DateTime, nullable=False)
    reporter_id = db.Column(db.String(36), db.ForeignKey('assignments.id'), nullable=True)
    status_id = db.Column(db.String(36), db.ForeignKey('station_statuses.id'), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    delete_flag = db.Column(db.Boolean, default=False)
    
    # Add these relationships after the columns
    reporter = db.relationship('Assignment', foreign_keys=[reporter_id], back_populates='status_reports')
    status = db.relationship('StationStatus', foreign_keys=[status_id], back_populates='status_reports')
    
    def __repr__(self):
        return f"<StatusReport {self.id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time.strftime("%H:%M") if self.time else None,
            'reporter_id': self.reporter_id,
            'status_id': self.status_id,
            'comment': self.comment,
            'delete_flag': self.delete_flag
        }
