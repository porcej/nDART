from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from functools import wraps
from . import auth_bp
from models import User
from extensions import db
from urllib.parse import urlparse
from sqlalchemy import func

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_uuid):
    """Load user by UUID."""
    return User.query.filter_by(uuid=user_uuid).first()

def role_required(*roles):
    """Decorator for views that require specific role(s)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if not current_user.has_any_role(roles):
                flash('You do not have permission to access this page.')
                return redirect(url_for('main_bp.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for views that require admin role."""
    return role_required('admin')(f)

@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        username = username.lower() if username else None
        user = User.query.filter(func.lower(User.name) == username, User.active == True).first()
        
        if user and user.check_password(password):
            # This is key: ensure login_user gets called correctly
            login_user(user, remember=('remember' in request.form))
            
            next_page = request.args.get('next')
            if next_page and urlparse(next_page).netloc == '':
                return redirect(next_page)
            return redirect(url_for('main_bp.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', username=current_user.name, is_admin=current_user.has_role('admin'), is_manager=current_user.has_role('manager'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Current password is incorrect.')
        return redirect(url_for('auth.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.')
        return redirect(url_for('auth.profile'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('Password updated successfully.')
    return redirect(url_for('auth.profile')) 