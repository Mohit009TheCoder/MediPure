from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import enum

SQLALCHEMY_DATABASE_URL = "sqlite:///./medipure.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String) # admin, doctor, patient
    
    # Common fields
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    zip = Column(String, nullable=True)
    area = Column(String, nullable=True) # For patients and doctors to search nearby
    
    # Patient-specific fields
    dob = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    blood_group = Column(String, nullable=True)
    disease_info = Column(String, nullable=True) # For patients: medical history
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    
    # Doctor-specific fields
    license_number = Column(String, nullable=True)
    specialty = Column(String, nullable=True) # For doctors: "Cardiologist", "Neurologist", etc.
    qualification = Column(String, nullable=True)
    experience = Column(Integer, nullable=True)
    clinic_name = Column(String, nullable=True)
    consultation_fee = Column(Integer, nullable=True)
    bio = Column(String, nullable=True)
    
    # Doctor statistics and ratings
    total_patients_treated = Column(Integer, default=0)
    patients_cured = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)  # Percentage
    rating = Column(Integer, default=0)  # Out of 5 (stored as 0-50 for precision)
    total_reviews = Column(Integer, default=0)
    awards = Column(String, nullable=True)  # Comma-separated awards
    certifications = Column(String, nullable=True)  # Additional certifications
    languages = Column(String, nullable=True)  # Languages spoken
    education = Column(String, nullable=True)  # Detailed education background

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_booked = Column(Boolean, default=False)

    doctor = relationship("User")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    slot_id = Column(Integer, ForeignKey("slots.id"))
    appointment_type = Column(String) # "video" or "physical"
    status = Column(String, default="scheduled") # scheduled, completed, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    reminder_sent = Column(Boolean, default=False)
    
    # Payment fields
    payment_status = Column(String, default="pending") # pending, paid, failed, refunded
    payment_amount = Column(Integer, nullable=True) # Amount in paise (INR)
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)
    payment_date = Column(DateTime, nullable=True)

    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    slot = relationship("Slot")

class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String, unique=True, index=True)  # Unique receipt number
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    
    # Payment details
    payment_amount = Column(Integer)  # Amount in paise
    payment_method = Column(String, default="Razorpay")
    razorpay_payment_id = Column(String)
    razorpay_order_id = Column(String)
    
    # Receipt details
    receipt_date = Column(DateTime, default=datetime.datetime.utcnow)
    tax_amount = Column(Integer, default=0)  # Tax in paise
    discount_amount = Column(Integer, default=0)  # Discount in paise
    total_amount = Column(Integer)  # Total in paise
    
    # Doctor earnings (full amount, fee deducted at withdrawal)
    doctor_earnings = Column(Integer)  # Full consultation fee goes to doctor initially
    
    # Additional info
    appointment_date = Column(DateTime)
    appointment_type = Column(String)
    consultation_fee = Column(Integer)
    
    # Relationships
    appointment = relationship("Appointment")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

class DoctorEarnings(Base):
    __tablename__ = "doctor_earnings"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    
    # Earnings summary
    total_consultations = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)  # Total amount received from patients (in paise)
    platform_fees_paid = Column(Integer, default=0)  # Total platform fees from withdrawals (in paise)
    total_earnings = Column(Integer, default=0)  # Gross earnings before withdrawal fees (in paise)
    
    # Withdrawal tracking
    withdrawn_amount = Column(Integer, default=0)  # Net amount paid to doctor (in paise)
    pending_amount = Column(Integer, default=0)  # Amount available for withdrawal (in paise)
    
    # Daily withdrawal tracking
    last_withdrawal_date = Column(String, nullable=True)  # Date in YYYY-MM-DD format
    withdrawals_today = Column(Integer, default=0)  # Count of withdrawals today
    
    # Platform earnings from penalties
    penalty_fees_collected = Column(Integer, default=0)  # Extra 5% from 3rd+ withdrawals
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship
    doctor = relationship("User", foreign_keys=[doctor_id])

class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    
    # Withdrawal details
    withdrawal_number = Column(String, unique=True, index=True)  # Unique withdrawal number
    gross_amount = Column(Integer)  # Amount before platform fee (in paise)
    platform_fee_percentage = Column(Integer)  # 10% or 15% based on frequency
    platform_fee_amount = Column(Integer)  # Platform fee deducted (in paise)
    net_amount = Column(Integer)  # Final amount to doctor after fee (in paise)
    status = Column(String, default="pending")  # pending, approved, processing, completed, rejected
    
    # Bank details
    account_holder_name = Column(String)
    account_number = Column(String)
    ifsc_code = Column(String)
    bank_name = Column(String)
    
    # Processing details
    requested_date = Column(DateTime, default=datetime.datetime.utcnow)
    approved_date = Column(DateTime, nullable=True)  # When admin approved
    processed_date = Column(DateTime, nullable=True)  # When payment completed
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who approved
    transaction_id = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    admin_notes = Column(String, nullable=True)  # Admin's internal notes
    
    # Withdrawal frequency tracking
    withdrawal_count_today = Column(Integer, default=0)  # Count of withdrawals on request date
    is_penalty_applied = Column(Boolean, default=False)  # True if 15% fee applied
    
    # Relationship
    doctor = relationship("User", foreign_keys=[doctor_id])
    approved_by_admin = relationship("User", foreign_keys=[approved_by])

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id])

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
