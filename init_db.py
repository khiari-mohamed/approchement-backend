#!/usr/bin/env python3
"""
Initialize database tables
"""

from database import create_tables, engine
from db_models.all_models import *
import os

def init_database():
    """Initialize database with all tables"""
    print("🗄️  Initializing database...")
    
    # Create all tables
    create_tables()
    
    print("✅ Database initialized successfully!")
    print(f"📍 Database location: {engine.url}")
    
    # Print created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"📊 Created {len(tables)} tables:")
    for table in tables:
        print(f"   - {table}")

if __name__ == "__main__":
    init_database()