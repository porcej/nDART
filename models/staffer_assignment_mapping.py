from extensions import db
from uuid import uuid4
from datetime import datetime, UTC

class StafferAssignmentMapping(db.Model):
    """Model for mapping imported staffer assignment names to nDART assignments"""
    __tablename__ = 'staffer_assignment_mappings'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    imported_name = db.Column(db.String(200), nullable=True, index=True)
    imported_short_code = db.Column(db.String(50), nullable=True, index=True)
    assignment_id = db.Column(db.String(36), db.ForeignKey('assignments.id'), nullable=True)
    is_manual_override = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        # At least one of imported_name or imported_short_code must be set
        db.CheckConstraint(
            'imported_name IS NOT NULL OR imported_short_code IS NOT NULL',
            name='ck_staffer_assignment_mappings_has_identifier'
        ),
    )
    
    # Relationships
    assignment = db.relationship('Assignment', foreign_keys=[assignment_id], backref='staffer_mappings')
    
    def __repr__(self):
        return f"<StafferAssignmentMapping {self.imported_name or self.imported_short_code} -> {self.assignment_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'imported_name': self.imported_name,
            'imported_short_code': self.imported_short_code,
            'assignment_id': self.assignment_id,
            'assignment_name': self.assignment.name if self.assignment else None,
            'is_manual_override': self.is_manual_override,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @staticmethod
    def get_mapping(imported_name=None, imported_short_code=None):
        """Get the mapping for an imported assignment name or short code"""
        if imported_short_code:
            mapping = StafferAssignmentMapping.query.filter_by(
                imported_short_code=imported_short_code
            ).first()
            if mapping:
                return mapping
        
        if imported_name:
            mapping = StafferAssignmentMapping.query.filter_by(
                imported_name=imported_name
            ).first()
            if mapping:
                return mapping
        
        return None
    
    @staticmethod
    def create_or_update_mapping(imported_name=None, imported_short_code=None, assignment_id=None, is_manual=False):
        """Create or update a mapping, but don't override manual mappings unless explicitly manual"""
        # Try to find existing mapping
        mapping = None
        
        if imported_short_code:
            mapping = StafferAssignmentMapping.query.filter_by(
                imported_short_code=imported_short_code
            ).first()
        
        if not mapping and imported_name:
            mapping = StafferAssignmentMapping.query.filter_by(
                imported_name=imported_name
            ).first()
        
        if mapping:
            # Don't override manual mappings with automatic ones
            if mapping.is_manual_override and not is_manual:
                return mapping
            
            # Update existing mapping
            if imported_name:
                mapping.imported_name = imported_name
            if imported_short_code:
                mapping.imported_short_code = imported_short_code
            mapping.assignment_id = assignment_id
            if is_manual:
                mapping.is_manual_override = True
            mapping.updated_at = datetime.now(UTC)
        else:
            # Create new mapping
            mapping = StafferAssignmentMapping(
                imported_name=imported_name,
                imported_short_code=imported_short_code,
                assignment_id=assignment_id,
                is_manual_override=is_manual
            )
            db.session.add(mapping)
        
        db.session.commit()
        return mapping

