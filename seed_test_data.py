import database
from auth import get_password_hash
from datetime import datetime, timedelta

def seed():
    db = next(database.get_db())
    
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
        consultation_fee=500,
        is_verified=True,
        is_approved=True
    )
    db.add(doctor)
    db.commit()

    # Create a slot for tomorrow (e.g. exactly 23 hours from now)
    tomorrow = datetime.utcnow() + timedelta(hours=23)
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
