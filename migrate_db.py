#!/usr/bin/env python3
"""
Database Migration Script
Adds new fields and tables for Cahier des Charges compliance
"""

from database import engine, Base
from db_models.all_models import *
from sqlalchemy import inspect

def migrate_database():
    """Run database migration to add new fields and tables"""
    print("🔄 Starting database migration...")
    
    # Get current tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"📊 Found {len(existing_tables)} existing tables")
    
    # Create all tables (will add new ones and update existing)
    print("🏗️  Creating/updating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify new tables
    inspector = inspect(engine)
    updated_tables = inspector.get_table_names()
    
    print(f"✅ Migration complete!")
    print(f"📊 Total tables: {len(updated_tables)}")
    
    # List new tables
    new_tables = set(updated_tables) - set(existing_tables)
    if new_tables:
        print(f"\n🆕 New tables added:")
        for table in new_tables:
            print(f"   - {table}")
    
    # Show all tables
    print(f"\n📋 All tables:")
    for table in sorted(updated_tables):
        columns = inspector.get_columns(table)
        print(f"   - {table} ({len(columns)} columns)")

if __name__ == "__main__":
    migrate_database()
