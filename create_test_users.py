#!/usr/bin/env python3
"""
Script to create test patient and doctor accounts
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database
import auth

# Create database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./medipure.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_users():
    db = SessionLocal()
    try:
        print("🔧 Creating test users...")
        print("=" * 60)
        
        # Create Test Patient
        existing_patient = db.query(database.User).filter(
            database.User.email == "patient@test.com"
        ).first()
        
        if not existing_patient:
            hashed_pwd = auth.get_password_hash("test123")
            patient = database.User(
                email="patient@test.com",
                hashed_password=hashed_pwd,
                full_name="John Patient",
                role="patient",
                phone="9876543210",
                city="Mumbai",
                area="Andheri",
                address="123 Test Street, Andheri West",
                gender="Male",
                blood_group="O+",
                dob="1990-01-15"
            )
            db.add(patient)
            print("✅ Patient account created")
        else:
            print("ℹ️  Patient account already exists")
        
        # Create Test Doctor
        existing_doctor = db.query(database.User).filter(
            database.User.email == "doctor@test.com"
        ).first()
        
        if not existing_doctor:
            hashed_pwd = auth.get_password_hash("test123")
            doctor = database.User(
                email="doctor@test.com",
                hashed_password=hashed_pwd,
                full_name="Dr. Sarah Smith",
                role="doctor",
                phone="9876543211",
                city="Mumbai",
                area="Andheri",
                address="456 Medical Plaza, Andheri East",
                specialty="General Physician",
                qualification="MBBS, MD",
                experience=10,
                consultation_fee=500,
                clinic_name="HealthCare Clinic",
                bio="Experienced general physician with 10 years of practice",
                license_number="MH-12345",
                rating=45,  # 4.5 out of 5 (stored as 45)
                total_reviews=50,
                total_patients_treated=500,
                patients_cured=450,
                success_rate=90
            )
            db.add(doctor)
            print("✅ Doctor account created")
        else:
            print("ℹ️  Doctor account already exists")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Test users created successfully!")
        print("\n📋 PATIENT CREDENTIALS:")
        print("   📧 Email: patient@test.com")
        print("   🔑 Password: test123")
        print("   👤 Name: John Patient")
        print("   📱 Phone: 9876543210")
        print("   📍 Location: Andheri, Mumbai")
        
        print("\n📋 DOCTOR CREDENTIALS:")
        print("   📧 Email: doctor@test.com")
        print("   🔑 Password: test123")
        print("   👤 Name: Dr. Sarah Smith")
        print("   🏥 Specialty: General Physician")
        print("   💰 Consultation Fee: ₹500")
        print("   📱 Phone: 9876543211")
        print("   📍 Location: Andheri, Mumbai")
        
        print("\n📋 ADMIN CREDENTIALS:")
        print("   📧 Email: admin@medipure.com")
        print("   🔑 Password: admin123")
        print("   👤 Name: System Administrator")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
