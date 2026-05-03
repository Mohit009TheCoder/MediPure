#!/usr/bin/env python3
"""
Script to remove all slots from the database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database

# Create database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./medipure.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def remove_all_slots():
    db = SessionLocal()
    try:
        print("🗑️  Removing all slots from the system...")
        print("=" * 60)
        
        # Count slots before deletion
        total_slots = db.query(database.Slot).count()
        booked_slots = db.query(database.Slot).filter(database.Slot.is_booked == True).count()
        available_slots = db.query(database.Slot).filter(database.Slot.is_booked == False).count()
        
        print(f"\n📊 Current Status:")
        print(f"   Total Slots: {total_slots}")
        print(f"   ├─ Booked: {booked_slots}")
        print(f"   └─ Available: {available_slots}")
        
        if total_slots == 0:
            print("\n✅ No slots found in the system")
            return
        
        # Delete all slots
        deleted = db.query(database.Slot).delete()
        db.commit()
        
        print(f"\n✅ Successfully deleted {deleted} slots")
        
        # Verify deletion
        remaining = db.query(database.Slot).count()
        print(f"\n📊 After Deletion:")
        print(f"   Remaining Slots: {remaining}")
        
        # Check users are still intact
        total_users = db.query(database.User).count()
        admins = db.query(database.User).filter(database.User.role == "admin").count()
        doctors = db.query(database.User).filter(database.User.role == "doctor").count()
        patients = db.query(database.User).filter(database.User.role == "patient").count()
        
        print(f"\n👥 User Accounts (Preserved):")
        print(f"   Total Users: {total_users}")
        print(f"   ├─ Admins: {admins}")
        print(f"   ├─ Doctors: {doctors}")
        print(f"   └─ Patients: {patients}")
        
        print("\n" + "=" * 60)
        print("✅ All slots removed successfully!")
        print("✅ User accounts preserved")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    remove_all_slots()
