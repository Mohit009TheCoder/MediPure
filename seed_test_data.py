import database
from auth import get_password_hash
from datetime import datetime, timedelta, timezone

def seed():
    db = next(database.get_db())
    
    # Check if users already exist
    existing_patient = db.query(database.User).filter(database.User.email == "patient@test.com").first()
    existing_doctor = db.query(database.User).filter(database.User.email == "doctor@test.com").first()
    
    if existing_patient or existing_doctor:
        # Re-hash passwords to bcrypt if they're still SHA-256
        for user, pwd in [(existing_patient, "patient123"), (existing_doctor, "doctor123")]:
            if user:
                pw = user.hashed_password  # Actual string value from DB
                if pw and len(pw) == 64 and all(c in '0123456789abcdef' for c in pw):
                    user.hashed_password = get_password_hash(pwd)
                    print(f"Re-hashed password for {user.email} to bcrypt")
        db.commit()
        print("Users already exist — passwords upgraded if needed.")
        return
    
    # Create patient
    patient = database.User(
        full_name="Test Patient",
        email="patient@test.com",
        hashed_password=get_password_hash("patient123"),
        role="patient",
        phone="1234567890",
        address="123 Patient St"
    )
    db.add(patient)
    
    # Create doctor
    doctor = database.User(
        full_name="Dr. Test",
        email="doctor@test.com",
        hashed_password=get_password_hash("doctor123"),
        role="doctor",
        phone="0987654321",
        address="456 Doctor Ave",
        specialty="Cardiology",
        experience=10,
        consultation_fee=500
    )
    db.add(doctor)
    db.commit()

    # Create a slot for tomorrow
    tomorrow = datetime.now(timezone.utc) + timedelta(hours=23)
    end_time = tomorrow + timedelta(minutes=30)

    slot = database.Slot(
        doctor_id=doctor.id,
        start_time=tomorrow,
        end_time=end_time,
        is_booked=True
    )
    db.add(slot)
    db.commit()

    # Create appointment
    appt = database.Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        slot_id=slot.id,
        appointment_type="video",
        status="scheduled"
    )
    db.add(appt)
    db.commit()
    print("Test data seeded!")

if __name__ == "__main__":
    seed()
