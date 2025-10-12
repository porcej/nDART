from extensions import db
from uuid import uuid4

class AppSettings(db.Model):
    """Model for application settings"""
    __tablename__ = 'app_settings'

    # Columns   
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_encrypted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<AppSettings {self.setting_key}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value if not self.is_encrypted else '***ENCRYPTED***',
            'description': self.description,
            'is_encrypted': self.is_encrypted
        }
    
    @staticmethod
    def get_setting(key, default=None):
        """Get a setting value by key"""
        setting = AppSettings.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default
    
    @staticmethod
    def set_setting(key, value, description=None, is_encrypted=False):
        """Set a setting value by key"""
        setting = AppSettings.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            if description:
                setting.description = description
            setting.is_encrypted = is_encrypted
        else:
            setting = AppSettings(
                setting_key=key,
                setting_value=value,
                description=description,
                is_encrypted=is_encrypted
            )
            db.session.add(setting)
        db.session.commit()
        return setting

