from extensions import db
from flask_login import UserMixin
from uuid import uuid4
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash


# Example of how to create roles and users
# # Create roles
# admin_role = Role(name='admin', description='Administrator with full access')
# manager_role = Role(name='manager', description='Manager with limited access')
# provider_role = Role(name='provider', description='Medical provider')

# # Create a user with multiple roles
# user = User(name='john_doe', id=1)
# user.add_role(admin_role)
# user.add_role(provider_role)

# # Check roles
# user.has_role('admin')  # True
# user.has_any_role(['manager', 'provider'])  # True
# user.has_all_roles(['admin', 'provider'])  # True


# @app.route('/admin')
# @admin_required
# def admin_dashboard():
#     return render_template('admin/dashboard.html')

# @app.route('/manager')
# @role_required('manager', 'admin')
# def manager_dashboard():
#     return render_template('manager/dashboard.html')

# Association table for User-Role relationship
user_roles = db.Table('user_roles',
    db.Column('user_id', db.String(36), 
              db.ForeignKey('users.id', name='fk_ur_user_id'),
              primary_key=True),
    db.Column('role_id', db.String(36), 
              db.ForeignKey('roles.id', name='fk_ur_role_id'),
              primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(UTC)),
    db.Column('created_by', db.String(36), 
              db.ForeignKey('users.id', name='fk_ur_created_by'),
              nullable=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(80), unique=True, nullable=False)
    person = db.Column(db.String(80))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    password_hash = db.Column(db.String(256))

    # Update the roles relationship with explicit join conditions
    roles = db.relationship(
        'Role', 
        secondary=user_roles,
        primaryjoin=(id == user_roles.c.user_id),
        secondaryjoin="Role.id == user_roles.c.role_id",
        foreign_keys=[
            user_roles.c.user_id,
            user_roles.c.role_id
        ],
        lazy='subquery',
        backref=db.backref('users', lazy=True)
    )

    def get_id(self):
        """Override get_id to return the uuid instead of an id."""
        return self.id

    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)

    def add_role(self, role):
        """Add a role to the user."""
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role):
        """Remove a role from the user."""
        if role in self.roles:
            self.roles.remove(role)

    def has_role(self, role_name):
        """Check if user has a specific role."""
        has_role = any(role.name == role_name for role in self.roles)
        return has_role

    def has_any_role(self, role_names):
        """Check if user has any of the specified roles."""
        return any(self.has_role(role_name) for role_name in role_names)

    def has_all_roles(self, role_names):
        """Check if user has all of the specified roles."""
        return all(self.has_role(role_name) for role_name in role_names)
    
    def get_username(self):
        return self.name
    
    def get_person(self):
        return self.person
    
    def set_person(self, person):
        self.person = person
    
    def user_stamp(self):
        return f'{self.person}-{self.name}' if self.person else f'{self.name}'

    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return self.active

    @property
    def is_admin(self):
        return self.has_role('admin')

    @property
    def is_manager(self):
        return self.has_role('manager')

    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'person': self.person,
            'active': self.active,
            'roles': [role.to_dict() for role in self.roles],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_admin': self.is_admin,
            'is_manager': self.is_manager
        }
    
    def __repr__(self):
        return f'<User {self.name}>'

   