import sys
import os

# Add the parent directory to the Python path to find the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import User, Role
from uuid import uuid4

def create_admin_user(username='admin', password='admin'):
    """Create an admin user with the admin role."""
    try:
        # Create Flask app and push an application context
        app = create_app()
        with app.app_context():
            print("Starting admin user creation...")
            
            # Check if admin role exists
            print("Checking for admin role...")
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                print("Creating admin role...")
                admin_role = Role(
                    id=str(uuid4()),
                    name='admin',
                    description='Administrator with full access',
                    active=True
                )
                db.session.add(admin_role)
                try:
                    db.session.commit()
                    print("Admin role created successfully")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating admin role: {str(e)}")
                    return
            else:
                print("Admin role already exists")

            # Check if admin user exists
            print("Checking for admin user...")
            admin_user = User.query.filter_by(name=username).first()
            if not admin_user:
                print("Creating admin user...")
                admin_user = User(
                    id=str(uuid4()),
                    name=username,
                    person='Administrator',
                    active=True,
                )
                admin_user.set_password(password)
                admin_user.add_role(admin_role)
                db.session.add(admin_user)
                try:
                    db.session.commit()
                    print(f"Admin user '{username}' created successfully")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating admin user: {str(e)}")
                    return
            else:
                print(f"Admin user '{username}' already exists")
                
            print("Admin user setup complete")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Make sure your database is properly configured and migrations have been run")

def main():
    """Main function to create admin user with custom credentials."""
    import argparse
    parser = argparse.ArgumentParser(description='Create admin user')
    parser.add_argument('--username', default='admin', help='Admin username')
    parser.add_argument('--password', default='admin', help='Admin password')
    
    args = parser.parse_args()
    create_admin_user(args.username, args.password)

if __name__ == '__main__':
    main() 