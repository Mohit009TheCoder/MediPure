from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pytz
import database
import auth
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Medipure - Doctor Appointment System")

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

def utc_to_ist(utc_dt):
    """Convert UTC datetime to IST"""
    if utc_dt.tzinfo is None:
        # If datetime is naive (no timezone), assume it's UTC
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(IST)

def ist_to_utc(ist_dt):
    """Convert IST datetime to UTC"""
    if ist_dt.tzinfo is None:
        # If datetime is naive, assume it's IST
        ist_dt = IST.localize(ist_dt)
    return ist_dt.astimezone(pytz.utc)

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Schemas
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str # admin, doctor, patient
    
    # Common fields
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    area: Optional[str] = None
    
    # Patient-specific fields
    dob: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    disease_info: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    # Doctor-specific fields
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[int] = None
    clinic_name: Optional[str] = None
    consultation_fee: Optional[int] = None
    bio: Optional[str] = None
    
    # Doctor statistics
    total_patients_treated: Optional[int] = 0
    patients_cured: Optional[int] = 0
    success_rate: Optional[int] = 0
    rating: Optional[int] = 0
    total_reviews: Optional[int] = 0
    awards: Optional[str] = None
    certifications: Optional[str] = None
    languages: Optional[str] = None
    education: Optional[str] = None

class SlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime

class AppointmentCreate(BaseModel):
    doctor_id: int
    slot_id: int
    appointment_type: str # video, physical

# AI Automation: Alert System
def send_ai_alert(email: str, message: str):
    # This simulates an AI alert system (Email/SMS/Push)
    print(f"AI ALERT to {email}: {message}")

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(database.User).filter(database.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = auth.get_password_hash(user.password)
    new_user = database.User(
        email=user.email,
        hashed_password=hashed_pwd,
        full_name=user.full_name,
        role=user.role,
        # Common fields
        phone=user.phone,
        address=user.address,
        city=user.city,
        zip=user.zip,
        area=user.area,
        # Patient fields
        dob=user.dob,
        gender=user.gender,
        blood_group=user.blood_group,
        disease_info=user.disease_info,
        emergency_contact_name=user.emergency_contact_name,
        emergency_contact_phone=user.emergency_contact_phone,
        # Doctor fields
        license_number=user.license_number,
        specialty=user.specialty,
        qualification=user.qualification,
        experience=user.experience,
        clinic_name=user.clinic_name,
        consultation_fee=user.consultation_fee,
        bio=user.bio,
        # Doctor statistics (with defaults)
        total_patients_treated=user.total_patients_treated or 0,
        patients_cured=user.patients_cured or 0,
        success_rate=user.success_rate or 0,
        rating=user.rating or 0,
        total_reviews=user.total_reviews or 0,
        awards=user.awards,
        certifications=user.certifications,
        languages=user.languages,
        education=user.education
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role,
        "user_id": user.id,
        "full_name": user.full_name
    }

# Doctor Endpoints
@app.post("/doctor/slots")
def add_slot(slot: SlotCreate, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can add slots")
    
    print(f"=== ADDING SLOT ===")
    print(f"Doctor ID: {current_user.id}")
    print(f"Start time received: {slot.start_time}")
    print(f"End time received: {slot.end_time}")
    print(f"Start time type: {type(slot.start_time)}")
    
    # Store datetime as-is (remove tzinfo if present)
    start_utc = slot.start_time.replace(tzinfo=None) if slot.start_time.tzinfo else slot.start_time
    end_utc = slot.end_time.replace(tzinfo=None) if slot.end_time.tzinfo else slot.end_time
    
    print(f"Start time to store: {start_utc}")
    print(f"End time to store: {end_utc}")
    
    new_slot = database.Slot(
        doctor_id=current_user.id,
        start_time=start_utc,
        end_time=end_utc
    )
    
    print(f"Slot object created: {new_slot}")
    
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    
    print(f"Slot saved with ID: {new_slot.id}")
    print(f"=== SLOT ADDED SUCCESSFULLY ===")
    
    return {
        "message": "Slot added successfully",
        "slot_id": new_slot.id,
        "start_time": new_slot.start_time.isoformat(),
        "end_time": new_slot.end_time.isoformat()
    }

@app.get("/doctor/slots")
def get_my_slots(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view their slots")
    
    # Get current time in UTC for comparison
    now_utc = datetime.utcnow()
    
    slots = db.query(database.Slot).filter(database.Slot.doctor_id == current_user.id).order_by(database.Slot.start_time).all()
    result = []
    for slot in slots:
        # Return times as-is (they're already in UTC from storage)
        # Frontend will handle display in local timezone
        
        # Check if slot is in the past (compare in UTC)
        is_past = slot.start_time <= now_utc
        
        result.append({
            "id": slot.id,
            "doctor_id": slot.doctor_id,
            "start_time": slot.start_time.isoformat(),  # Send UTC time to frontend
            "end_time": slot.end_time.isoformat(),      # Send UTC time to frontend
            "is_booked": slot.is_booked,
            "is_past": is_past
        })
    return result

@app.delete("/doctor/slots/all")
def delete_all_slots(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Delete all unbooked slots for the current doctor"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can delete slots")
    
    # Only delete unbooked slots
    deleted = db.query(database.Slot).filter(
        database.Slot.doctor_id == current_user.id,
        database.Slot.is_booked == False
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return {
        "message": f"Deleted {deleted} unbooked slots",
        "deleted": deleted
    }

@app.delete("/doctor/slots/bulk")
def delete_multiple_slots(slot_ids: List[int], current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Delete multiple slots at once"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can delete slots")
    
    deleted_count = 0
    failed_count = 0
    errors = []
    
    for slot_id in slot_ids:
        slot = db.query(database.Slot).filter(
            database.Slot.id == slot_id,
            database.Slot.doctor_id == current_user.id
        ).first()
        
        if not slot:
            failed_count += 1
            errors.append(f"Slot {slot_id} not found")
            continue
        
        if slot.is_booked:
            failed_count += 1
            errors.append(f"Slot {slot_id} is booked and cannot be deleted")
            continue
        
        db.delete(slot)
        deleted_count += 1
    
    db.commit()
    
    return {
        "message": f"Deleted {deleted_count} slots",
        "deleted": deleted_count,
        "failed": failed_count,
        "errors": errors if errors else None
    }

@app.delete("/doctor/slots/{slot_id}")
def delete_slot(slot_id: int, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can delete slots")
    
    slot = db.query(database.Slot).filter(
        database.Slot.id == slot_id,
        database.Slot.doctor_id == current_user.id
    ).first()
    
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="Cannot delete a booked slot")
    
    db.delete(slot)
    db.commit()
    return {"message": "Slot deleted successfully"}

@app.get("/doctor/appointments")
def get_doctor_appointments(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    appointments = db.query(database.Appointment).filter(database.Appointment.doctor_id == current_user.id).all()
    result = []
    for appt in appointments:
        patient = db.query(database.User).filter(database.User.id == appt.patient_id).first()
        slot = db.query(database.Slot).filter(database.Slot.id == appt.slot_id).first()
        result.append({
            "id": appt.id,
            "patient_id": appt.patient_id,
            "patient_name": patient.full_name if patient else "Unknown",
            "doctor_id": appt.doctor_id,
            "slot_id": appt.slot_id,
            "start_time": slot.start_time.isoformat() if slot else None,
            "end_time": slot.end_time.isoformat() if slot else None,
            "appointment_type": appt.appointment_type,
            "status": appt.status,
            "created_at": appt.created_at.isoformat()
        })
    return result

# Patient Endpoints
@app.get("/doctors/search")
def search_doctors(area: Optional[str] = None, disease: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(database.User).filter(database.User.role == "doctor")
    if area:
        query = query.filter(database.User.area.ilike(f"%{area}%"))
    if disease:
        query = query.filter(database.User.specialty.ilike(f"%{disease}%"))
    return query.all()

@app.get("/doctors/top-rated")
def get_top_doctors(limit: int = 10, db: Session = Depends(database.get_db)):
    """Get top-rated doctors based on success rate and patient reviews"""
    doctors = db.query(database.User).filter(
        database.User.role == "doctor"
    ).order_by(
        database.User.success_rate.desc(),
        database.User.rating.desc(),
        database.User.total_patients_treated.desc()
    ).limit(limit).all()
    
    result = []
    for doc in doctors:
        result.append({
            "id": doc.id,
            "full_name": doc.full_name,
            "specialty": doc.specialty,
            "qualification": doc.qualification,
            "experience": doc.experience,
            "clinic_name": doc.clinic_name,
            "area": doc.area,
            "city": doc.city,
            "consultation_fee": doc.consultation_fee,
            "bio": doc.bio,
            "total_patients_treated": doc.total_patients_treated,
            "patients_cured": doc.patients_cured,
            "success_rate": doc.success_rate,
            "rating": doc.rating / 10.0 if doc.rating else 0,  # Convert to 0-5 scale
            "total_reviews": doc.total_reviews,
            "awards": doc.awards,
            "certifications": doc.certifications,
            "languages": doc.languages,
            "education": doc.education,
            "phone": doc.phone
        })
    return result

@app.get("/doctors/{doctor_id}/profile")
def get_doctor_profile(doctor_id: int, db: Session = Depends(database.get_db)):
    """Get detailed doctor profile"""
    doctor = db.query(database.User).filter(
        database.User.id == doctor_id,
        database.User.role == "doctor"
    ).first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return {
        "id": doctor.id,
        "full_name": doctor.full_name,
        "email": doctor.email,
        "specialty": doctor.specialty,
        "qualification": doctor.qualification,
        "experience": doctor.experience,
        "clinic_name": doctor.clinic_name,
        "area": doctor.area,
        "city": doctor.city,
        "address": doctor.address,
        "phone": doctor.phone,
        "consultation_fee": doctor.consultation_fee,
        "bio": doctor.bio,
        "license_number": doctor.license_number,
        "total_patients_treated": doctor.total_patients_treated,
        "patients_cured": doctor.patients_cured,
        "success_rate": doctor.success_rate,
        "rating": doctor.rating / 10.0 if doctor.rating else 0,
        "total_reviews": doctor.total_reviews,
        "awards": doctor.awards.split(",") if doctor.awards else [],
        "certifications": doctor.certifications.split(",") if doctor.certifications else [],
        "languages": doctor.languages.split(",") if doctor.languages else [],
        "education": doctor.education
    }

@app.get("/doctors/{doctor_id}/slots")
def get_doctor_slots(doctor_id: int, db: Session = Depends(database.get_db)):
    """Get available slots for a doctor (only future slots that are not booked)"""
    # Get current time in UTC for comparison
    now_utc = datetime.utcnow()
    
    # Filter: not booked AND start time is in the future
    slots = db.query(database.Slot).filter(
        database.Slot.doctor_id == doctor_id, 
        database.Slot.is_booked == False,
        database.Slot.start_time > now_utc  # Only future slots
    ).order_by(database.Slot.start_time).all()
    
    result = []
    for slot in slots:
        # Return times as-is (UTC), frontend will handle local display
        result.append({
            "id": slot.id,
            "doctor_id": slot.doctor_id,
            "start_time": slot.start_time.isoformat(),  # Send UTC time to frontend
            "end_time": slot.end_time.isoformat(),      # Send UTC time to frontend
            "is_booked": slot.is_booked
        })
    return result

@app.post("/appointments/book")
def book_appointment(appt: AppointmentCreate, background_tasks: BackgroundTasks, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can book appointments")
    
    slot = db.query(database.Slot).filter(database.Slot.id == appt.slot_id).first()
    if not slot or slot.is_booked:
        raise HTTPException(status_code=400, detail="Slot unavailable")
    
    # Check if slot is in the past (compare in UTC)
    now_utc = datetime.utcnow()
    if slot.start_time <= now_utc:
        raise HTTPException(status_code=400, detail="Cannot book past time slots")
    
    new_appt = database.Appointment(
        patient_id=current_user.id,
        doctor_id=appt.doctor_id,
        slot_id=appt.slot_id,
        appointment_type=appt.appointment_type
    )
    slot.is_booked = True
    db.add(new_appt)
    db.commit()

    # AI Automation Trigger
    background_tasks.add_task(send_ai_alert, current_user.email, f"Your {appt.appointment_type} appointment is booked for {slot.start_time.strftime('%I:%M %p, %d %b %Y')}!")
    
    return {"message": "Appointment booked successfully"}

# Profile Endpoints
@app.get("/profile/me")
def get_profile(current_user: database.User = Depends(auth.get_current_user)):
    profile_data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "phone": current_user.phone,
        "address": current_user.address,
        "city": current_user.city,
        "zip": current_user.zip,
        "area": current_user.area
    }
    
    # Add role-specific fields
    if current_user.role == "patient":
        profile_data.update({
            "dob": current_user.dob,
            "gender": current_user.gender,
            "blood_group": current_user.blood_group,
            "disease_info": current_user.disease_info,
            "emergency_contact_name": current_user.emergency_contact_name,
            "emergency_contact_phone": current_user.emergency_contact_phone
        })
    elif current_user.role == "doctor":
        profile_data.update({
            "license_number": current_user.license_number,
            "specialty": current_user.specialty,
            "qualification": current_user.qualification,
            "experience": current_user.experience,
            "clinic_name": current_user.clinic_name,
            "consultation_fee": current_user.consultation_fee,
            "bio": current_user.bio
        })
    
    return profile_data

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    area: Optional[str] = None
    specialty: Optional[str] = None
    disease_info: Optional[str] = None
    bio: Optional[str] = None
    consultation_fee: Optional[int] = None

@app.put("/profile/update")
def update_profile(profile: ProfileUpdate, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if profile.full_name:
        current_user.full_name = profile.full_name
    if profile.phone:
        current_user.phone = profile.phone
    if profile.address:
        current_user.address = profile.address
    if profile.city:
        current_user.city = profile.city
    if profile.zip:
        current_user.zip = profile.zip
    if profile.area:
        current_user.area = profile.area
    if profile.specialty:
        current_user.specialty = profile.specialty
    if profile.disease_info:
        current_user.disease_info = profile.disease_info
    if profile.bio:
        current_user.bio = profile.bio
    if profile.consultation_fee is not None:
        current_user.consultation_fee = profile.consultation_fee
    
    db.commit()
    return {"message": "Profile updated successfully"}

@app.get("/patient/appointments")
def get_patient_appointments(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    appointments = db.query(database.Appointment).filter(database.Appointment.patient_id == current_user.id).all()
    result = []
    for appt in appointments:
        doctor = db.query(database.User).filter(database.User.id == appt.doctor_id).first()
        slot = db.query(database.Slot).filter(database.Slot.id == appt.slot_id).first()
        result.append({
            "id": appt.id,
            "patient_id": appt.patient_id,
            "doctor_id": appt.doctor_id,
            "doctor_name": doctor.full_name if doctor else "Unknown",
            "doctor_specialty": doctor.specialty if doctor else "General Physician",
            "slot_id": appt.slot_id,
            "start_time": slot.start_time.isoformat() if slot else None,
            "end_time": slot.end_time.isoformat() if slot else None,
            "appointment_type": appt.appointment_type,
            "status": appt.status,
            "created_at": appt.created_at.isoformat()
        })
    return result

# Admin Endpoints
@app.get("/admin/stats")
def get_admin_stats(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_doctors = db.query(database.User).filter(database.User.role == "doctor").count()
    total_patients = db.query(database.User).filter(database.User.role == "patient").count()
    total_appointments = db.query(database.Appointment).count()
    
    # Calculate today's appointments
    from datetime import datetime, timedelta
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    appointments_today = db.query(database.Appointment).join(database.Slot).filter(
        database.Slot.start_time >= today_start,
        database.Slot.start_time < today_end
    ).count()
    
    # Calculate revenue (sum of consultation fees from completed appointments)
    completed_appointments = db.query(database.Appointment).filter(
        database.Appointment.status == "completed"
    ).all()
    
    total_revenue = 0
    for appt in completed_appointments:
        doctor = db.query(database.User).filter(database.User.id == appt.doctor_id).first()
        if doctor and doctor.consultation_fee:
            total_revenue += doctor.consultation_fee
    
    return {
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "appointments_today": appointments_today,
        "total_revenue": total_revenue,
        "scheduled_appointments": db.query(database.Appointment).filter(database.Appointment.status == "scheduled").count(),
        "completed_appointments": db.query(database.Appointment).filter(database.Appointment.status == "completed").count(),
        "cancelled_appointments": db.query(database.Appointment).filter(database.Appointment.status == "cancelled").count()
    }

@app.get("/admin/doctors")
def get_all_doctors(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    doctors = db.query(database.User).filter(database.User.role == "doctor").all()
    result = []
    for doc in doctors:
        # Count appointments for this doctor
        appointments_count = db.query(database.Appointment).filter(database.Appointment.doctor_id == doc.id).count()
        
        result.append({
            "id": doc.id,
            "full_name": doc.full_name,
            "email": doc.email,
            "phone": doc.phone,
            "specialty": doc.specialty,
            "qualification": doc.qualification,
            "experience": doc.experience,
            "clinic_name": doc.clinic_name,
            "area": doc.area,
            "city": doc.city,
            "consultation_fee": doc.consultation_fee,
            "license_number": doc.license_number,
            "total_patients_treated": doc.total_patients_treated,
            "patients_cured": doc.patients_cured,
            "success_rate": doc.success_rate,
            "rating": doc.rating / 10.0 if doc.rating else 0,
            "total_reviews": doc.total_reviews,
            "appointments_count": appointments_count
        })
    return result

@app.get("/admin/patients")
def get_all_patients(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    patients = db.query(database.User).filter(database.User.role == "patient").all()
    result = []
    for patient in patients:
        # Count appointments for this patient
        appointments_count = db.query(database.Appointment).filter(database.Appointment.patient_id == patient.id).count()
        
        result.append({
            "id": patient.id,
            "full_name": patient.full_name,
            "email": patient.email,
            "phone": patient.phone,
            "address": patient.address,
            "city": patient.city,
            "area": patient.area,
            "zip": patient.zip,
            "dob": patient.dob,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "disease_info": patient.disease_info,
            "emergency_contact_name": patient.emergency_contact_name,
            "emergency_contact_phone": patient.emergency_contact_phone,
            "appointments_count": appointments_count
        })
    return result

@app.get("/admin/appointments")
def get_all_appointments(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    appointments = db.query(database.Appointment).all()
    result = []
    for appt in appointments:
        patient = db.query(database.User).filter(database.User.id == appt.patient_id).first()
        doctor = db.query(database.User).filter(database.User.id == appt.doctor_id).first()
        slot = db.query(database.Slot).filter(database.Slot.id == appt.slot_id).first()
        
        result.append({
            "id": appt.id,
            "patient_id": appt.patient_id,
            "patient_name": patient.full_name if patient else "Unknown",
            "patient_email": patient.email if patient else "Unknown",
            "patient_phone": patient.phone if patient else "Unknown",
            "doctor_id": appt.doctor_id,
            "doctor_name": doctor.full_name if doctor else "Unknown",
            "doctor_specialty": doctor.specialty if doctor else "General Physician",
            "doctor_phone": doctor.phone if doctor else "Unknown",
            "slot_id": appt.slot_id,
            "start_time": slot.start_time.isoformat() if slot else None,
            "end_time": slot.end_time.isoformat() if slot else None,
            "appointment_type": appt.appointment_type,
            "status": appt.status,
            "created_at": appt.created_at.isoformat(),
            "consultation_fee": doctor.consultation_fee if doctor else 0
        })
    return result

@app.get("/admin/recent-activity")
def get_recent_activity(limit: int = 10, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get recent appointments
    appointments = db.query(database.Appointment).order_by(database.Appointment.created_at.desc()).limit(limit).all()
    
    result = []
    for appt in appointments:
        patient = db.query(database.User).filter(database.User.id == appt.patient_id).first()
        doctor = db.query(database.User).filter(database.User.id == appt.doctor_id).first()
        slot = db.query(database.Slot).filter(database.Slot.id == appt.slot_id).first()
        
        result.append({
            "id": appt.id,
            "type": "appointment",
            "patient_name": patient.full_name if patient else "Unknown",
            "doctor_name": doctor.full_name if doctor else "Unknown",
            "doctor_specialty": doctor.specialty if doctor else "General Physician",
            "appointment_type": appt.appointment_type,
            "status": appt.status,
            "start_time": slot.start_time.isoformat() if slot else None,
            "created_at": appt.created_at.isoformat()
        })
    
    return result

# Frontend Routes
@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.get("/login")
def read_login():
    return FileResponse("static/login.html")

@app.get("/dashboard")
def read_dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/profile")
def read_profile():
    return FileResponse("static/profile.html")

@app.get("/top-doctors")
def read_top_doctors():
    return FileResponse("static/top-doctors.html")

@app.get("/privacy")
def read_privacy():
    return FileResponse("static/privacy.html")

@app.get("/terms")
def read_terms():
    return FileResponse("static/terms.html")

@app.get("/contact")
def read_contact():
    return FileResponse("static/contact.html")

@app.get("/calendar")
def read_calendar():
    from fastapi.responses import FileResponse
    response = FileResponse("static/calendar.html")
    # Force browser to reload (no cache)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/services")
def read_services():
    return FileResponse("static/services.html")

@app.get("/test")
def read_test():
    return FileResponse("test_calendar.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
