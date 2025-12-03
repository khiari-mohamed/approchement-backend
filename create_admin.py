#!/usr/bin/env python3
"""
Create default admin user
"""

from database import SessionLocal
from services.auth_service import create_user
from db_models.users import User

def create_admin_user():
    """Create default admin user if not exists"""
    db = SessionLocal()
    
    try:
        # Check if admin exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("✅ Admin user already exists")
            return
        
        # Create admin user
        admin_user = create_user(
            db=db,
            username="admin",
            email="admin@company.com",
            password="admin123",  # Change this in production!
            full_name="Administrateur",
            role="admin"
        )
        
        print("✅ Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: admin123 (CHANGE THIS!)")
        print(f"   Role: {admin_user.role}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()