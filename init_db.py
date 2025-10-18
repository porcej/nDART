#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Initialization Script

This script initializes the database with all required tables.
Run this script if you need to recreate the database from scratch.

Usage:
    python init_db.py
    docker-compose exec ndart python init_db.py
"""

from app import create_app
from extensions import db
from models import (
    User, Agency, Event, Assignment, Observation, ObservationsCategory, 
    StationStatus, StafferAROVolunteer, StafferAssignmentMapping, 
    StatusReport, ChatRoom, ChatMessage, Role, AppSettings
)

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✅ All tables created successfully")
            
            # List all tables
            result = db.session.execute(db.text('SELECT name FROM sqlite_master WHERE type="table"'))
            tables = [row[0] for row in result.fetchall()]
            print(f"📊 Database tables: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)
