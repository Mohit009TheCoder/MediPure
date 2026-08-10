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
import razorpay
import razorpay_config
import hmac
import hashlib
import random
import string

app = FastAPI(title="Medipure - Doctor Appointment System")

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(razorpay_config.RAZORPAY_KEY_ID, razorpay_config.RAZORPAY_KEY_SECRET))

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

def generate_receipt_number():
    """Generate unique receipt number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"RCP-{timestamp}-{random_str}"

def generate_withdrawal_number():
    """Generate unique withdrawal number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"WD-{timestamp}-{random_str}"

def calculate_withdrawal_fee(amount, withdrawal_count_today):
    """
    Calculate platform fee based on withdrawal frequency
    - First 2 withdrawals per day: 10% fee
    - 3rd+ withdrawals per day: 15% fee (5% penalty)
    """
    if withdrawal_count_today < 2:
        fee_percentage = 10
        is_penalty = False
    else:
        fee_percentage = 15
        is_penalty = True
    
    platform_fee = int(amount * fee_percentage / 100)
    net_amount = amount - platform_fee
    
    return {
        'fee_percentage': fee_percentage,
        'platform_fee': platform_fee,
        'net_amount': net_amount,
        'is_penalty': is_penalty,
        'penalty_amount': int(amount * 5 / 100) if is_penalty else 0
    }

def update_doctor_earnings(db: Session, doctor_id: int, consultation_fee: int):
    """Update doctor earnings after successful payment - NO platform fee at this stage"""
    # Get or create doctor earnings record
    earnings = db.query(database.DoctorEarnings).filter(
        database.DoctorEarnings.doctor_id == doctor_id
    ).first()
    
    if not earnings:
        earnings = database.DoctorEarnings(
            doctor_id=doctor_id,
            total_consultations=0,
            total_revenue=0,
            platform_fees_paid=0,
            total_earnings=0,
            withdrawn_amount=0,
            pending_amount=0,
            withdrawals_today=0,
            penalty_fees_collected=0
        )
        db.add(earnings)
    
    # Update earnings - full consultation fee goes to doctor
    earnings.total_consultations += 1
    earnings.total_revenue += consultation_fee
    earnings.total_earnings += consultation_fee  # Full amount
    earnings.pending_amount += consultation_fee  # Full amount available
    earnings.last_updated = datetime.utcnow()
    
    db.commit()
    return consultation_fee  # Return full amount

def get_withdrawal_count_today(db: Session, doctor_id: int):
    """Get count of withdrawals requested today by doctor"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Count withdrawals with status pending, approved, processing, or completed today
    count = db.query(database.Withdrawal).filter(
        database.Withdrawal.doctor_id == doctor_id,
        database.Withdrawal.requested_date >= datetime.strptime(today, "%Y-%m-%d"),
        database.Withdrawal.status.in_(['pending', 'approved', 'processing', 'completed'])
    ).count()
    
    return count
    earnings.last_updated = datetime.utcnow()
    
    db.commit()
    return platform_fee, doctor_earnings

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

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    appointment_id: int

class WithdrawalRequest(BaseModel):
    amount: int  # Amount in rupees
    account_holder_name: str
    account_number: str
    ifsc_code: str
    bank_name: str

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
            "patient_phone": patient.phone if patient else "N/A",
            "patient_email": patient.email if patient else "N/A",
            "doctor_id": appt.doctor_id,
            "slot_id": appt.slot_id,
            "start_time": slot.start_time.isoformat() if slot else None,
            "end_time": slot.end_time.isoformat() if slot else None,
            "appointment_type": appt.appointment_type,
            "status": appt.status,
            "payment_status": appt.payment_status,
            "created_at": appt.created_at.isoformat()
        })
    return result

class AppointmentStatusUpdate(BaseModel):
    status: str  # "completed", "cancelled"
    notes: Optional[str] = None

@app.put("/doctor/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int, 
    status_update: AppointmentStatusUpdate,
    current_user: database.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    """Mark appointment as completed or cancelled (doctor only)"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can update appointment status")
    
    # Get appointment
    appointment = db.query(database.Appointment).filter(
        database.Appointment.id == appointment_id,
        database.Appointment.doctor_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Validate status
    if status_update.status not in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Status must be 'completed' or 'cancelled'")
    
    # Check if appointment is paid
    if appointment.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Cannot update status of unpaid appointment")
    
    # Check if already completed (prevent double-counting)
    if appointment.status == "completed":
        raise HTTPException(status_code=400, detail="Appointment already marked as completed")
    
    # Update status
    old_status = appointment.status
    appointment.status = status_update.status
    
    # If marking as completed, add money to doctor's earnings
    if status_update.status == "completed" and old_status != "completed":
        # Get or create doctor earnings record
        earnings = db.query(database.DoctorEarnings).filter(
            database.DoctorEarnings.doctor_id == current_user.id
        ).first()
        
        if not earnings:
            earnings = database.DoctorEarnings(
                doctor_id=current_user.id,
                total_consultations=0,
                total_revenue=0,
                total_earnings=0,
                pending_amount=0,
                withdrawn_amount=0,
                platform_fees_paid=0,
                withdrawals_today=0,
                penalty_fees_collected=0
            )
            db.add(earnings)
        
        # Get consultation fee from payment receipt
        receipt = db.query(database.PaymentReceipt).filter(
            database.PaymentReceipt.appointment_id == appointment.id
        ).first()
        
        if receipt:
            consultation_fee = receipt.consultation_fee  # Amount in paise
            
            # Add to doctor's earnings (full amount, fee deducted at withdrawal)
            earnings.total_consultations += 1
            earnings.total_revenue += consultation_fee
            earnings.total_earnings += consultation_fee
            earnings.pending_amount += consultation_fee
            earnings.last_updated = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Appointment marked as {status_update.status}",
        "appointment_id": appointment.id,
        "old_status": old_status,
        "new_status": appointment.status,
        "earnings_updated": status_update.status == "completed"
    }

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

@app.post("/appointments/create-order")
def create_appointment_order(appt: AppointmentCreate, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Create appointment and Razorpay order for payment"""
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can book appointments")
    
    # Get slot details
    slot = db.query(database.Slot).filter(database.Slot.id == appt.slot_id).first()
    if not slot or slot.is_booked:
        raise HTTPException(status_code=400, detail="Slot unavailable")
    
    # Check if slot is in the past
    now_utc = datetime.utcnow()
    if slot.start_time <= now_utc:
        raise HTTPException(status_code=400, detail="Cannot book past time slots")
    
    # Get doctor details for consultation fee
    doctor = db.query(database.User).filter(database.User.id == appt.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    consultation_fee = doctor.consultation_fee or 500  # Default fee if not set
    amount_in_paise = consultation_fee * 100  # Convert to paise
    
    # Create appointment record (pending payment)
    new_appt = database.Appointment(
        patient_id=current_user.id,
        doctor_id=appt.doctor_id,
        slot_id=appt.slot_id,
        appointment_type=appt.appointment_type,
        status="pending_payment",
        payment_status="pending",
        payment_amount=amount_in_paise
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    
    # Create Razorpay order
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": razorpay_config.CURRENCY,
            "receipt": f"appt_{new_appt.id}",
            "notes": {
                "appointment_id": new_appt.id,
                "patient_id": current_user.id,
                "doctor_id": appt.doctor_id,
                "patient_name": current_user.full_name,
                "doctor_name": doctor.full_name
            }
        })
        
        # Update appointment with order ID
        new_appt.razorpay_order_id = razorpay_order['id']
        db.commit()
        
        return {
            "success": True,
            "appointment_id": new_appt.id,
            "order_id": razorpay_order['id'],
            "amount": consultation_fee,
            "currency": razorpay_config.CURRENCY,
            "key_id": razorpay_config.RAZORPAY_KEY_ID,
            "doctor_name": doctor.full_name,
            "doctor_specialty": doctor.specialty,
            "slot_time": slot.start_time.isoformat(),
            "appointment_type": appt.appointment_type
        }
    except Exception as e:
        # Rollback appointment if order creation fails
        db.delete(new_appt)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create payment order: {str(e)}")

@app.post("/appointments/verify-payment")
def verify_payment(payment: PaymentVerification, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Verify Razorpay payment and confirm appointment"""
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can verify payments")
    
    # Get appointment
    appointment = db.query(database.Appointment).filter(
        database.Appointment.id == payment.appointment_id,
        database.Appointment.patient_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify signature
    generated_signature = hmac.new(
        razorpay_config.RAZORPAY_KEY_SECRET.encode(),
        f"{payment.razorpay_order_id}|{payment.razorpay_payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    if generated_signature != payment.razorpay_signature:
        # Payment verification failed
        appointment.payment_status = "failed"
        appointment.status = "cancelled"
        db.commit()
        raise HTTPException(status_code=400, detail="Payment verification failed")
    
    # Payment verified successfully
    appointment.razorpay_payment_id = payment.razorpay_payment_id
    appointment.razorpay_signature = payment.razorpay_signature
    appointment.payment_status = "paid"
    appointment.payment_date = datetime.utcnow()
    appointment.status = "scheduled"
    
    # Mark slot as booked
    slot = db.query(database.Slot).filter(database.Slot.id == appointment.slot_id).first()
    if slot:
        slot.is_booked = True
    
    # Get doctor and slot details
    doctor = db.query(database.User).filter(database.User.id == appointment.doctor_id).first()
    
    # Generate Payment Receipt
    receipt_number = generate_receipt_number()
    
    # Calculate amounts
    consultation_fee = appointment.payment_amount  # Already in paise
    tax_amount = 0  # No tax for now
    discount_amount = 0  # No discount
    total_amount = consultation_fee + tax_amount - discount_amount
    
    # Doctor gets FULL amount initially (fee deducted at withdrawal)
    doctor_earnings = consultation_fee
    
    # Get current time in IST
    now_ist = get_ist_now()
    
    # Create receipt record
    receipt = database.PaymentReceipt(
        receipt_number=receipt_number,
        appointment_id=appointment.id,
        patient_id=current_user.id,
        doctor_id=appointment.doctor_id,
        payment_amount=consultation_fee,
        payment_method="Razorpay",
        razorpay_payment_id=payment.razorpay_payment_id,
        razorpay_order_id=payment.razorpay_order_id,
        receipt_date=now_ist.replace(tzinfo=None),  # Store as naive datetime
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        doctor_earnings=doctor_earnings,  # Full amount
        appointment_date=slot.start_time if slot else None,
        appointment_type=appointment.appointment_type,
        consultation_fee=consultation_fee
    )
    
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    
    # Update doctor earnings (full amount, no fee yet)
    update_doctor_earnings(db, appointment.doctor_id, consultation_fee)
    db.refresh(receipt)
    
    # Update doctor earnings
    update_doctor_earnings(db, appointment.doctor_id, consultation_fee)
    
    return {
        "success": True,
        "message": "Payment verified and appointment confirmed",
        "appointment_id": appointment.id,
        "payment_id": payment.razorpay_payment_id,
        "receipt_id": receipt.id,
        "receipt_number": receipt_number,
        "doctor_name": doctor.full_name if doctor else "Unknown",
        "appointment_type": appointment.appointment_type,
        "status": appointment.status
    }

@app.post("/appointments/book")
def book_appointment(appt: AppointmentCreate, background_tasks: BackgroundTasks, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Legacy endpoint - redirects to payment flow"""
    raise HTTPException(
        status_code=400, 
        detail="Please use /appointments/create-order endpoint for booking with payment"
    )

@app.get("/appointments/{appointment_id}/payment-status")
def get_payment_status(appointment_id: int, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get payment status for an appointment"""
    appointment = db.query(database.Appointment).filter(database.Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check if user has access to this appointment
    if current_user.role == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor" and appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role not in ["patient", "doctor", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "appointment_id": appointment.id,
        "payment_status": appointment.payment_status,
        "payment_amount": appointment.payment_amount / 100 if appointment.payment_amount else 0,  # Convert to rupees
        "razorpay_order_id": appointment.razorpay_order_id,
        "razorpay_payment_id": appointment.razorpay_payment_id,
        "payment_date": appointment.payment_date.isoformat() if appointment.payment_date else None
    }

# Receipt Endpoints
@app.get("/receipts/{receipt_id}")
def get_receipt(receipt_id: int, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get receipt details by receipt ID"""
    receipt = db.query(database.PaymentReceipt).filter(database.PaymentReceipt.id == receipt_id).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Check access
    if current_user.role == "patient" and receipt.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor" and receipt.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role not in ["patient", "doctor", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get related data
    patient = db.query(database.User).filter(database.User.id == receipt.patient_id).first()
    doctor = db.query(database.User).filter(database.User.id == receipt.doctor_id).first()
    appointment = db.query(database.Appointment).filter(database.Appointment.id == receipt.appointment_id).first()
    
    # Convert UTC times to IST for display
    receipt_date_ist = utc_to_ist(receipt.receipt_date) if receipt.receipt_date else None
    # appointment_date is already in IST (from slot.start_time), no conversion needed
    appointment_date_ist = receipt.appointment_date
    
    return {
        "receipt_id": receipt.id,
        "receipt_number": receipt.receipt_number,
        "receipt_date": receipt_date_ist.isoformat() if receipt_date_ist else None,
        "appointment_id": receipt.appointment_id,
        "appointment_type": receipt.appointment_type,
        "appointment_date": appointment_date_ist.isoformat() if appointment_date_ist else None,
        "patient": {
            "id": patient.id,
            "name": patient.full_name,
            "email": patient.email,
            "phone": patient.phone
        } if patient else None,
        "doctor": {
            "id": doctor.id,
            "name": doctor.full_name,
            "specialty": doctor.specialty,
            "clinic_name": doctor.clinic_name
        } if doctor else None,
        "payment": {
            "consultation_fee": receipt.consultation_fee / 100,  # Convert to rupees
            "tax_amount": receipt.tax_amount / 100,
            "discount_amount": receipt.discount_amount / 100,
            "total_amount": receipt.total_amount / 100,
            "payment_method": receipt.payment_method,
            "razorpay_payment_id": receipt.razorpay_payment_id,
            "razorpay_order_id": receipt.razorpay_order_id
        }
    }

@app.get("/receipts/appointment/{appointment_id}")
def get_receipt_by_appointment(appointment_id: int, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get receipt by appointment ID"""
    receipt = db.query(database.PaymentReceipt).filter(
        database.PaymentReceipt.appointment_id == appointment_id
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found for this appointment")
    
    # Check access
    if current_user.role == "patient" and receipt.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor" and receipt.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role not in ["patient", "doctor", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get related data
    patient = db.query(database.User).filter(database.User.id == receipt.patient_id).first()
    doctor = db.query(database.User).filter(database.User.id == receipt.doctor_id).first()
    
    # Convert UTC times to IST for display
    receipt_date_ist = utc_to_ist(receipt.receipt_date) if receipt.receipt_date else None
    # appointment_date is already in IST (from slot.start_time), no conversion needed
    appointment_date_ist = receipt.appointment_date
    
    return {
        "receipt_id": receipt.id,
        "receipt_number": receipt.receipt_number,
        "receipt_date": receipt_date_ist.isoformat() if receipt_date_ist else None,
        "appointment_id": receipt.appointment_id,
        "appointment_type": receipt.appointment_type,
        "appointment_date": appointment_date_ist.isoformat() if appointment_date_ist else None,
        "patient": {
            "id": patient.id,
            "name": patient.full_name,
            "email": patient.email,
            "phone": patient.phone
        } if patient else None,
        "doctor": {
            "id": doctor.id,
            "name": doctor.full_name,
            "specialty": doctor.specialty,
            "clinic_name": doctor.clinic_name
        } if doctor else None,
        "payment": {
            "consultation_fee": receipt.consultation_fee / 100,
            "tax_amount": receipt.tax_amount / 100,
            "discount_amount": receipt.discount_amount / 100,
            "total_amount": receipt.total_amount / 100,
            "payment_method": receipt.payment_method,
            "razorpay_payment_id": receipt.razorpay_payment_id,
            "razorpay_order_id": receipt.razorpay_order_id
        }
    }

@app.get("/patient/receipts")
def get_patient_receipts(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get all receipts for current patient"""
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can access this endpoint")
    
    receipts = db.query(database.PaymentReceipt).filter(
        database.PaymentReceipt.patient_id == current_user.id
    ).order_by(database.PaymentReceipt.receipt_date.desc()).all()
    
    result = []
    for receipt in receipts:
        doctor = db.query(database.User).filter(database.User.id == receipt.doctor_id).first()
        
        # Convert UTC to IST for display
        receipt_date_ist = utc_to_ist(receipt.receipt_date) if receipt.receipt_date else None
        
        result.append({
            "receipt_id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "receipt_date": receipt_date_ist.isoformat() if receipt_date_ist else None,
            "appointment_id": receipt.appointment_id,
            "doctor_name": doctor.full_name if doctor else "Unknown",
            "doctor_specialty": doctor.specialty if doctor else "N/A",
            "total_amount": receipt.total_amount / 100,
            "payment_method": receipt.payment_method,
            "appointment_type": receipt.appointment_type
        })
    
    return result

@app.get("/admin/receipts")
def get_all_receipts(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get all receipts (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    receipts = db.query(database.PaymentReceipt).order_by(
        database.PaymentReceipt.receipt_date.desc()
    ).all()
    
    result = []
    for receipt in receipts:
        patient = db.query(database.User).filter(database.User.id == receipt.patient_id).first()
        doctor = db.query(database.User).filter(database.User.id == receipt.doctor_id).first()
        
        # Convert UTC to IST for display
        receipt_date_ist = utc_to_ist(receipt.receipt_date) if receipt.receipt_date else None
        
        result.append({
            "receipt_id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "receipt_date": receipt_date_ist.isoformat() if receipt_date_ist else None,
            "appointment_id": receipt.appointment_id,
            "patient_name": patient.full_name if patient else "Unknown",
            "patient_email": patient.email if patient else "N/A",
            "doctor_name": doctor.full_name if doctor else "Unknown",
            "doctor_specialty": doctor.specialty if doctor else "N/A",
            "total_amount": receipt.total_amount / 100,
            "payment_method": receipt.payment_method,
            "appointment_type": receipt.appointment_type,
            "razorpay_payment_id": receipt.razorpay_payment_id
        })
    
    return result

# Doctor Earnings Endpoints
@app.get("/doctor/earnings")
def get_doctor_earnings(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get earnings summary for current doctor - READ ONLY"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access earnings")
    
    earnings = db.query(database.DoctorEarnings).filter(
        database.DoctorEarnings.doctor_id == current_user.id
    ).first()
    
    if not earnings:
        # Create initial earnings record
        earnings = database.DoctorEarnings(
            doctor_id=current_user.id,
            total_consultations=0,
            total_revenue=0,
            platform_fees_paid=0,
            total_earnings=0,
            withdrawn_amount=0,
            pending_amount=0,
            withdrawals_today=0,
            penalty_fees_collected=0
        )
        db.add(earnings)
        db.commit()
        db.refresh(earnings)
    
    # Get today's withdrawal count
    withdrawal_count_today = get_withdrawal_count_today(db, current_user.id)
    
    # Calculate next withdrawal fee
    next_fee_calc = calculate_withdrawal_fee(earnings.pending_amount, withdrawal_count_today)
    
    return {
        "doctor_id": earnings.doctor_id,
        "total_consultations": earnings.total_consultations,
        "total_revenue": earnings.total_revenue / 100,  # Total from patients
        "total_earnings": earnings.total_earnings / 100,  # Gross earnings (before withdrawal fees)
        "platform_fees_paid": earnings.platform_fees_paid / 100,  # Fees paid on withdrawals
        "penalty_fees_paid": earnings.penalty_fees_collected / 100,  # Extra 5% penalties
        "withdrawn_amount": earnings.withdrawn_amount / 100,  # Net amount received
        "pending_amount": earnings.pending_amount / 100,  # Available for withdrawal
        "withdrawals_today": withdrawal_count_today,
        "next_withdrawal_fee_percentage": next_fee_calc['fee_percentage'],
        "next_withdrawal_will_be_penalty": next_fee_calc['is_penalty'],
        "last_updated": earnings.last_updated.isoformat() if earnings.last_updated else None,
        "note": "Platform fee is deducted when you request withdrawal. First 2 withdrawals per day: 10% fee. 3rd+ withdrawals: 15% fee."
    }

@app.get("/doctor/earnings/breakdown")
def get_earnings_breakdown(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get detailed earnings breakdown by appointment - READ ONLY"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access earnings")
    
    receipts = db.query(database.PaymentReceipt).filter(
        database.PaymentReceipt.doctor_id == current_user.id
    ).order_by(database.PaymentReceipt.receipt_date.desc()).all()
    
    result = []
    for receipt in receipts:
        patient = db.query(database.User).filter(database.User.id == receipt.patient_id).first()
        receipt_date_ist = utc_to_ist(receipt.receipt_date) if receipt.receipt_date else None
        
        result.append({
            "receipt_id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "receipt_date": receipt_date_ist.isoformat() if receipt_date_ist else None,
            "patient_name": patient.full_name if patient else "Unknown",
            "consultation_fee": receipt.consultation_fee / 100,
            "your_earnings": receipt.doctor_earnings / 100,  # Full amount (fee deducted at withdrawal)
            "appointment_type": receipt.appointment_type,
            "note": "Platform fee will be deducted when you withdraw"
        })
    
    return result

# Withdrawal Endpoints
@app.post("/doctor/withdraw")
def request_withdrawal(withdrawal: WithdrawalRequest, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Request withdrawal of earnings - Admin will approve and process"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can request withdrawals")
    
    # Get doctor earnings
    earnings = db.query(database.DoctorEarnings).filter(
        database.DoctorEarnings.doctor_id == current_user.id
    ).first()
    
    if not earnings:
        raise HTTPException(status_code=404, detail="No earnings found")
    
    # Convert amount to paise
    gross_amount = withdrawal.amount * 100
    
    # Check if sufficient balance
    if gross_amount > earnings.pending_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. Available: ₹{earnings.pending_amount / 100}"
        )
    
    # Minimum withdrawal amount
    if withdrawal.amount < 100:
        raise HTTPException(status_code=400, detail="Minimum withdrawal amount is ₹100")
    
    # Get withdrawal count today
    withdrawal_count_today = get_withdrawal_count_today(db, current_user.id)
    
    # Calculate platform fee based on frequency
    fee_calc = calculate_withdrawal_fee(gross_amount, withdrawal_count_today)
    
    # Create withdrawal request (pending admin approval)
    withdrawal_number = generate_withdrawal_number()
    new_withdrawal = database.Withdrawal(
        doctor_id=current_user.id,
        withdrawal_number=withdrawal_number,
        gross_amount=gross_amount,
        platform_fee_percentage=fee_calc['fee_percentage'],
        platform_fee_amount=fee_calc['platform_fee'],
        net_amount=fee_calc['net_amount'],
        status="pending",  # Waiting for admin approval
        account_holder_name=withdrawal.account_holder_name,
        account_number=withdrawal.account_number,
        ifsc_code=withdrawal.ifsc_code,
        bank_name=withdrawal.bank_name,
        requested_date=datetime.utcnow(),
        withdrawal_count_today=withdrawal_count_today + 1,
        is_penalty_applied=fee_calc['is_penalty']
    )
    
    db.add(new_withdrawal)
    db.commit()
    db.refresh(new_withdrawal)
    
    # Note: Balance NOT deducted yet - only deducted when admin approves
    
    # Prepare response message
    fee_message = f"{fee_calc['fee_percentage']}% platform fee"
    if fee_calc['is_penalty']:
        fee_message += f" (includes 5% penalty for 3rd+ withdrawal today)"
    
    return {
        "success": True,
        "message": "Withdrawal request submitted for admin approval",
        "withdrawal_id": new_withdrawal.id,
        "withdrawal_number": withdrawal_number,
        "gross_amount": withdrawal.amount,
        "platform_fee_percentage": fee_calc['fee_percentage'],
        "platform_fee": fee_calc['platform_fee'] / 100,
        "net_amount": fee_calc['net_amount'] / 100,
        "status": "pending",
        "note": f"Admin will review and process your request. {fee_message}. You will receive ₹{fee_calc['net_amount'] / 100} after approval.",
        "is_penalty_applied": fee_calc['is_penalty'],
        "withdrawal_count_today": withdrawal_count_today + 1
    }

@app.get("/doctor/withdrawals")
def get_withdrawal_history(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get withdrawal history for current doctor - READ ONLY"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access withdrawal history")
    
    withdrawals = db.query(database.Withdrawal).filter(
        database.Withdrawal.doctor_id == current_user.id
    ).order_by(database.Withdrawal.requested_date.desc()).all()
    
    result = []
    for w in withdrawals:
        requested_date_ist = utc_to_ist(w.requested_date) if w.requested_date else None
        approved_date_ist = utc_to_ist(w.approved_date) if w.approved_date else None
        processed_date_ist = utc_to_ist(w.processed_date) if w.processed_date else None
        
        result.append({
            "withdrawal_id": w.id,
            "withdrawal_number": w.withdrawal_number,
            "gross_amount": w.gross_amount / 100,
            "platform_fee_percentage": w.platform_fee_percentage,
            "platform_fee": w.platform_fee_amount / 100,
            "net_amount": w.net_amount / 100,
            "status": w.status,
            "is_penalty_applied": w.is_penalty_applied,
            "withdrawal_count_today": w.withdrawal_count_today,
            "account_holder_name": w.account_holder_name,
            "account_number": "XXXX" + w.account_number[-4:] if w.account_number else "N/A",  # Masked
            "bank_name": w.bank_name,
            "requested_date": requested_date_ist.isoformat() if requested_date_ist else None,
            "approved_date": approved_date_ist.isoformat() if approved_date_ist else None,
            "processed_date": processed_date_ist.isoformat() if processed_date_ist else None,
            "transaction_id": w.transaction_id,
            "notes": w.notes
        })
    
    return result

# Admin Withdrawal Management
@app.get("/admin/withdrawals")
def get_all_withdrawals(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Get all withdrawal requests with detailed calculations (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    withdrawals = db.query(database.Withdrawal).order_by(
        database.Withdrawal.requested_date.desc()
    ).all()
    
    result = []
    for w in withdrawals:
        doctor = db.query(database.User).filter(database.User.id == w.doctor_id).first()
        requested_date_ist = utc_to_ist(w.requested_date) if w.requested_date else None
        approved_date_ist = utc_to_ist(w.approved_date) if w.approved_date else None
        processed_date_ist = utc_to_ist(w.processed_date) if w.processed_date else None
        
        # Get doctor's current earnings
        earnings = db.query(database.DoctorEarnings).filter(
            database.DoctorEarnings.doctor_id == w.doctor_id
        ).first()
        
        result.append({
            "withdrawal_id": w.id,
            "withdrawal_number": w.withdrawal_number,
            "doctor_id": w.doctor_id,
            "doctor_name": doctor.full_name if doctor else "Unknown",
            "doctor_email": doctor.email if doctor else "N/A",
            "doctor_phone": doctor.phone if doctor else "N/A",
            "gross_amount": w.gross_amount / 100,
            "platform_fee_percentage": w.platform_fee_percentage,
            "platform_fee": w.platform_fee_amount / 100,
            "net_amount": w.net_amount / 100,
            "status": w.status,
            "is_penalty_applied": w.is_penalty_applied,
            "withdrawal_count_today": w.withdrawal_count_today,
            "account_holder_name": w.account_holder_name,
            "account_number": w.account_number,
            "ifsc_code": w.ifsc_code,
            "bank_name": w.bank_name,
            "requested_date": requested_date_ist.isoformat() if requested_date_ist else None,
            "approved_date": approved_date_ist.isoformat() if approved_date_ist else None,
            "processed_date": processed_date_ist.isoformat() if processed_date_ist else None,
            "transaction_id": w.transaction_id,
            "notes": w.notes,
            "admin_notes": w.admin_notes,
            "doctor_pending_balance": earnings.pending_amount / 100 if earnings else 0,
            "doctor_total_earnings": earnings.total_earnings / 100 if earnings else 0
        })
    
    return result

class WithdrawalApproval(BaseModel):
    action: str  # "approve" or "reject"
    admin_notes: Optional[str] = None

@app.post("/admin/withdrawals/{withdrawal_id}/approve")
def approve_withdrawal(withdrawal_id: int, approval: WithdrawalApproval, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Approve or reject withdrawal request (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    withdrawal = db.query(database.Withdrawal).filter(database.Withdrawal.id == withdrawal_id).first()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail=f"Withdrawal is already {withdrawal.status}")
    
    # Get doctor earnings
    earnings = db.query(database.DoctorEarnings).filter(
        database.DoctorEarnings.doctor_id == withdrawal.doctor_id
    ).first()
    
    if not earnings:
        raise HTTPException(status_code=404, detail="Doctor earnings not found")
    
    if approval.action == "approve":
        # Check if doctor still has sufficient balance
        if withdrawal.gross_amount > earnings.pending_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Doctor has ₹{earnings.pending_amount / 100}, requested ₹{withdrawal.gross_amount / 100}"
            )
        
        # Deduct from pending balance
        earnings.pending_amount -= withdrawal.gross_amount
        
        # Add platform fee to earnings
        earnings.platform_fees_paid += withdrawal.platform_fee_amount
        
        # Track penalty fees separately
        if withdrawal.is_penalty_applied:
            penalty_amount = int(withdrawal.gross_amount * 5 / 100)
            earnings.penalty_fees_collected += penalty_amount
        
        # Update withdrawal status
        withdrawal.status = "approved"
        withdrawal.approved_date = datetime.utcnow()
        withdrawal.approved_by = current_user.id
        if approval.admin_notes:
            withdrawal.admin_notes = approval.admin_notes
        
        earnings.last_updated = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Withdrawal approved successfully",
            "withdrawal_id": withdrawal.id,
            "withdrawal_number": withdrawal.withdrawal_number,
            "gross_amount": withdrawal.gross_amount / 100,
            "platform_fee": withdrawal.platform_fee_amount / 100,
            "net_amount": withdrawal.net_amount / 100,
            "status": "approved",
            "note": f"Deducted ₹{withdrawal.gross_amount / 100} from doctor's balance. Platform fee: ₹{withdrawal.platform_fee_amount / 100}. Doctor will receive: ₹{withdrawal.net_amount / 100}"
        }
    
    elif approval.action == "reject":
        # Reject withdrawal - no balance changes
        withdrawal.status = "rejected"
        withdrawal.approved_date = datetime.utcnow()
        withdrawal.approved_by = current_user.id
        if approval.admin_notes:
            withdrawal.admin_notes = approval.admin_notes
        else:
            withdrawal.admin_notes = "Rejected by admin"
        
        db.commit()
        
        return {
            "success": True,
            "message": "Withdrawal rejected",
            "withdrawal_id": withdrawal.id,
            "withdrawal_number": withdrawal.withdrawal_number,
            "status": "rejected",
            "note": "No balance changes made"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")

class WithdrawalUpdate(BaseModel):
    status: str  # "processing", "completed", "failed"
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

@app.put("/admin/withdrawals/{withdrawal_id}")
def update_withdrawal_status(withdrawal_id: int, update: WithdrawalUpdate, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Update withdrawal payment status after approval (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    withdrawal = db.query(database.Withdrawal).filter(database.Withdrawal.id == withdrawal_id).first()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status not in ["approved", "processing"]:
        raise HTTPException(status_code=400, detail=f"Cannot update withdrawal with status: {withdrawal.status}")
    
    # Update status
    old_status = withdrawal.status
    withdrawal.status = update.status
    withdrawal.processed_date = datetime.utcnow()
    
    if update.transaction_id:
        withdrawal.transaction_id = update.transaction_id
    
    if update.notes:
        withdrawal.notes = update.notes
    
    # If payment completed, update withdrawn amount
    if update.status == "completed" and old_status != "completed":
        earnings = db.query(database.DoctorEarnings).filter(
            database.DoctorEarnings.doctor_id == withdrawal.doctor_id
        ).first()
        
        if earnings:
            earnings.withdrawn_amount += withdrawal.net_amount  # Net amount paid to doctor
            earnings.last_updated = datetime.utcnow()
    
    # If payment failed, refund to doctor's pending amount
    elif update.status == "failed":
        earnings = db.query(database.DoctorEarnings).filter(
            database.DoctorEarnings.doctor_id == withdrawal.doctor_id
        ).first()
        
        if earnings:
            # Refund gross amount back to pending
            earnings.pending_amount += withdrawal.gross_amount
            # Refund platform fee
            earnings.platform_fees_paid -= withdrawal.platform_fee_amount
            # Refund penalty if applicable
            if withdrawal.is_penalty_applied:
                penalty_amount = int(withdrawal.gross_amount * 5 / 100)
                earnings.penalty_fees_collected -= penalty_amount
            earnings.last_updated = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Withdrawal {update.status}",
        "withdrawal_id": withdrawal.id,
        "withdrawal_number": withdrawal.withdrawal_number,
        "status": withdrawal.status,
        "net_amount_paid": withdrawal.net_amount / 100 if update.status == "completed" else 0
    }

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
            "consultation_fee": doctor.consultation_fee if doctor else 0,
            "slot_id": appt.slot_id,
            "start_time": slot.start_time.isoformat() if slot else None,
            "end_time": slot.end_time.isoformat() if slot else None,
            "appointment_type": appt.appointment_type,
            "status": appt.status,
            "payment_status": appt.payment_status,
            "payment_amount": appt.payment_amount / 100 if appt.payment_amount else 0,
            "razorpay_payment_id": appt.razorpay_payment_id,
            "created_at": appt.created_at.isoformat()
        })
    return result

# Analytics & Patient Visit Tracking Endpoints
@app.get("/analytics/patient-visits")
def get_patient_visit_analytics(
    doctor_id: Optional[int] = None,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Returns analytics on patient visit frequency, repeat rates, and detailed visit timelines.
    """
    query = db.query(database.Appointment)
    
    if current_user.role == "doctor":
        query = query.filter(database.Appointment.doctor_id == current_user.id)
    elif current_user.role == "patient":
        query = query.filter(database.Appointment.patient_id == current_user.id)
    elif current_user.role == "admin" and doctor_id:
        query = query.filter(database.Appointment.doctor_id == doctor_id)
        
    all_appointments = query.all()
    
    # Group appointments by patient_id
    patient_appts = {}
    for appt in all_appointments:
        if appt.patient_id not in patient_appts:
            patient_appts[appt.patient_id] = []
        patient_appts[appt.patient_id].append(appt)
        
    patients_list = []
    total_appointments = len(all_appointments)
    repeat_patients_count = 0
    first_time_patients_count = 0
    frequent_patients_count = 0
    
    completed_visits = 0
    scheduled_visits = 0
    cancelled_visits = 0
    
    physical_count = 0
    video_count = 0

    for p_id, appts in patient_appts.items():
        patient_user = db.query(database.User).filter(database.User.id == p_id).first()
        if not patient_user:
            continue
            
        # Sort appointments chronologically
        appts_sorted = []
        for appt in appts:
            slot = db.query(database.Slot).filter(database.Slot.id == appt.slot_id).first()
            time_val = slot.start_time if slot and slot.start_time else appt.created_at
            appts_sorted.append((time_val, appt, slot))
            
        appts_sorted.sort(key=lambda x: x[0])
        
        visit_count = len(appts_sorted)
        if visit_count == 1:
            first_time_patients_count += 1
            visit_category = "First-Time (1 Visit)"
        elif visit_count == 2:
            repeat_patients_count += 1
            visit_category = "Repeat (2 Visits)"
        else:
            repeat_patients_count += 1
            frequent_patients_count += 1
            visit_category = f"Frequent ({visit_count} Visits)"
            
        doctors_visited_map = {}
        status_breakdown = {"completed": 0, "scheduled": 0, "cancelled": 0}
        consultation_types = {"physical": 0, "video": 0}
        visit_history = []
        
        for idx, (t_val, appt, slot) in enumerate(appts_sorted, start=1):
            doc = db.query(database.User).filter(database.User.id == appt.doctor_id).first()
            doc_name = doc.full_name if doc else "Unknown Doctor"
            doc_specialty = doc.specialty if doc else "General Physician"
            
            doctors_visited_map[doc_name] = doctors_visited_map.get(doc_name, 0) + 1
            
            st = appt.status or "scheduled"
            if st in status_breakdown:
                status_breakdown[st] += 1
            if st == "completed":
                completed_visits += 1
            elif st == "scheduled":
                scheduled_visits += 1
            elif st == "cancelled":
                cancelled_visits += 1
                
            atype = appt.appointment_type or "physical"
            if atype in consultation_types:
                consultation_types[atype] += 1
            if atype == "physical":
                physical_count += 1
            else:
                video_count += 1
                
            visit_history.append({
                "visit_number": idx,
                "appointment_id": appt.id,
                "doctor_id": appt.doctor_id,
                "doctor_name": doc_name,
                "doctor_specialty": doc_specialty,
                "date": t_val.isoformat() if t_val else appt.created_at.isoformat(),
                "appointment_type": atype,
                "status": st,
                "payment_status": appt.payment_status,
                "payment_amount": (appt.payment_amount / 100) if appt.payment_amount else (doc.consultation_fee if doc else 0)
            })
            
        doctors_visited = [{"doctor_name": name, "visit_count": count} for name, count in doctors_visited_map.items()]
        
        patients_list.append({
            "patient_id": patient_user.id,
            "patient_name": patient_user.full_name,
            "patient_email": patient_user.email,
            "patient_phone": patient_user.phone or "N/A",
            "gender": patient_user.gender or "N/A",
            "blood_group": patient_user.blood_group or "N/A",
            "disease_info": patient_user.disease_info or "None",
            "total_visits": visit_count,
            "visit_category": visit_category,
            "first_visit_date": visit_history[0]["date"] if visit_history else None,
            "last_visit_date": visit_history[-1]["date"] if visit_history else None,
            "doctors_visited": doctors_visited,
            "consultation_types": consultation_types,
            "status_breakdown": status_breakdown,
            "visit_history": visit_history
        })

    patients_list.sort(key=lambda x: x["total_visits"], reverse=True)
    
    total_unique_patients = len(patients_list)
    repeat_pct = round((repeat_patients_count / total_unique_patients * 100), 1) if total_unique_patients > 0 else 0
    avg_visits = round((total_appointments / total_unique_patients), 1) if total_unique_patients > 0 else 0
    
    return {
        "summary": {
            "total_unique_patients": total_unique_patients,
            "total_appointments": total_appointments,
            "repeat_patients_count": repeat_patients_count,
            "repeat_patient_percentage": repeat_pct,
            "avg_visits_per_patient": avg_visits,
            "first_time_patients_count": first_time_patients_count,
            "frequent_patients_count": frequent_patients_count,
            "completed_visits": completed_visits,
            "scheduled_visits": scheduled_visits,
            "cancelled_visits": cancelled_visits,
            "physical_visits": physical_count,
            "video_visits": video_count
        },
        "patients": patients_list
    }

# Admin Endpoints
@app.get("/admin/stats")
def get_admin_stats(current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from sqlalchemy import func
    
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
    
    # Calculate total revenue from payment receipts (actual payments received)
    total_revenue = db.query(func.sum(database.PaymentReceipt.consultation_fee)).scalar() or 0
    
    # Calculate platform fees collected from withdrawals
    total_platform_fees = db.query(func.sum(database.DoctorEarnings.platform_fees_paid)).scalar() or 0
    
    # Calculate pending platform fees (from pending doctor earnings)
    total_pending_earnings = db.query(func.sum(database.DoctorEarnings.pending_amount)).scalar() or 0
    
    # Calculate total withdrawn by doctors
    total_withdrawn = db.query(func.sum(database.DoctorEarnings.withdrawn_amount)).scalar() or 0
    
    return {
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "appointments_today": appointments_today,
        "total_revenue": total_revenue,  # Total payments received from patients
        "platform_fees_collected": total_platform_fees,  # Platform fees collected from withdrawals
        "pending_doctor_earnings": total_pending_earnings,  # Money waiting to be withdrawn
        "total_withdrawn": total_withdrawn,  # Money paid to doctors
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

@app.get("/payment")
def read_payment():
    return FileResponse("static/payment.html")

@app.get("/receipt")
def read_receipt():
    return FileResponse("static/receipt.html")

@app.get("/doctor-payment-terms")
def read_doctor_payment_terms():
    return FileResponse("static/doctor-payment-terms.html")

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
