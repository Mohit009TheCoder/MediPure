#!/usr/bin/env python3
"""
Script to create the default admin account
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database
import auth

# Create database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./medipure.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(database.User).filter(
            database.User.email == "admin@medipure.com"
        ).first()
        
        if existing_admin:
            print("ℹ️  Admin account already exists")
            print(f"   Email: {existing_admin.email}")
            print(f"   Name: {existing_admin.full_name}")
            return
        
        # Create admin account
        hashed_pwd = auth.get_password_hash("admin123")
        admin = database.User(
            email="admin@medipure.com",
            hashed_password=hashed_pwd,
            full_name="System Administrator",
            role="admin"
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✅ Admin account created successfully!")
        print(f"\n📧 Email: admin@medipure.com")
        print(f"🔑 Password: admin123")
        print(f"👤 Name: System Administrator")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Creating default admin account...")
    print("=" * 60)
    create_admin()
