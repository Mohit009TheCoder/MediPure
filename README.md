# Medipure - AI-Powered Doctor Appointment System

Medipure is a modern, premium healthcare platform that connects patients with doctors for both video consultations and physical appointments.

## Features
- **Three User Roles**: Admin, Doctor, and Patient
- **Search & Filter**: Find doctors by area (nearby) and specialty/disease
- **Slot Management**: Doctors can upload and manage their availability slots
- **Booking System**: Patients can book slots for video calls or physical visits
- **AI Automation**: 
  - **Alert System**: Background tasks send automated booking reminders
  - **AI Health Diagnosis**: Symptom analysis tool that recommends the right specialist
- **Professional Design**: Premium medical-themed UI with smooth animations
- **Complete Profile Management**: Users can view and update their profiles
- **Appointment Tracking**: View all appointments with detailed information

## Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Vanilla HTML5, CSS3 (Premium Design), JavaScript
- **Auth**: Simple token-based authentication with secure password hashing

## Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download the repository**

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```
   
   Or if using the virtual environment:
   ```bash
   source venv/bin/activate && python main.py
   ```

5. **Open your browser** at `http://localhost:8000`

## Usage

### Default Admin Credentials
**Email:** `admin@medipure.com`  
**Password:** `admin123`

### For Admins
1. **Login** with admin credentials
2. **View System Overview** - total doctors, patients, appointments, and revenue
3. **View All Doctors** - complete list with details, ratings, and statistics
4. **View All Patients** - patient information, medical history, and appointments
5. **View All Appointments** - comprehensive appointment tracking with patient and doctor details
6. **System Analytics** - detailed statistics and system information
7. **Recent Activity** - monitor latest appointments and bookings

### For Patients
1. **Register** as a patient with your personal and medical information
2. **Login** with your credentials
3. **Search for doctors** by location and specialty
4. **Use AI Health Check** to get specialist recommendations based on symptoms
5. **Book appointments** for video consultations or physical visits
6. **View your appointments** on the dashboard
7. **Manage your profile** with medical history and emergency contacts

### For Doctors
1. **Register** as a doctor with your license, specialty, and clinic information
2. **Login** with your credentials
3. **Manage availability slots** - add time slots when you're available
4. **View appointments** - see all scheduled consultations
5. **Track patients** - view patient information and appointment history
6. **Update your profile** with bio, consultation fees, and specialization

### For Admins
1. **Login** with admin credentials
2. **View system overview** - total doctors, patients, and appointments
3. **Monitor platform activity** and analytics

## API Endpoints

### Authentication
- `POST /register` - Register a new user (patient/doctor/admin)
- `POST /token` - Login and get JWT token

### Patient Endpoints
- `GET /doctors/search` - Search doctors by area and specialty
- `GET /doctors/{doctor_id}/slots` - Get available slots for a doctor
- `POST /appointments/book` - Book an appointment
- `GET /patient/appointments` - Get all patient appointments

### Doctor Endpoints
- `POST /doctor/slots` - Add availability slot
- `GET /doctor/slots` - Get all doctor's slots
- `GET /doctor/appointments` - Get all doctor appointments

### Profile Endpoints
- `GET /profile/me` - Get current user profile
- `PUT /profile/update` - Update user profile

### Admin Endpoints
- `GET /admin/stats` - Get system statistics (doctors, patients, appointments, revenue)
- `GET /admin/doctors` - Get all doctors with complete details
- `GET /admin/patients` - Get all patients with medical information
- `GET /admin/appointments` - Get all appointments with full details
- `GET /admin/recent-activity` - Get recent system activity

## Database Schema

### Users Table
- Common fields: email, password, full_name, role, phone, address, city, zip, area
- Patient-specific: dob, gender, blood_group, disease_info, emergency contacts
- Doctor-specific: license_number, specialty, qualification, experience, clinic_name, consultation_fee, bio

### Slots Table
- doctor_id, start_time, end_time, is_booked

### Appointments Table
- patient_id, doctor_id, slot_id, appointment_type (video/physical), status, created_at

## Features in Detail

### AI Health Assistant
The AI Health Assistant analyzes patient symptoms and recommends appropriate specialists:
- Analyzes symptom descriptions
- Suggests relevant medical specialties
- Helps patients find the right doctor quickly

### Slot Management
Doctors can:
- Add multiple time slots for availability
- View all slots (booked and available)
- Slots are automatically marked as booked when appointments are made

### Appointment System
- Supports both video and physical consultations
- Real-time availability checking
- Appointment status tracking (scheduled, completed, cancelled)
- Detailed appointment information with doctor/patient names and times

### Profile Management
- Role-specific profile fields
- Update personal information
- View appointment statistics
- Emergency contact information for patients
- Professional credentials for doctors

## Security Features
- Password hashing using SHA256
- Simple token-based authentication
- Protected API endpoints
- Role-based access control

## Project Structure
```
Medipure/
├── main.py              # FastAPI application and API endpoints
├── auth.py              # Authentication and JWT handling
├── database.py          # Database models and configuration
├── config.py            # Application configuration
├── requirements.txt     # Python dependencies
├── medipure.db         # SQLite database (auto-created)
├── static/             # Frontend files
│   ├── index.html      # Landing page
│   ├── login.html      # Login/Registration page
│   ├── dashboard.html  # User dashboard
│   ├── profile.html    # Profile management
│   ├── index.css       # Main styles
│   ├── footer-styles.css
│   ├── logo.svg
│   ├── privacy.html    # Privacy policy
│   ├── terms.html      # Terms of service
│   └── contact.html    # Contact page
└── README.md           # This file
```

## Troubleshooting

### Port 8000 already in use
If you get an error that port 8000 is already in use:
```bash
# On macOS/Linux
lsof -ti:8000 | xargs kill -9

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Module not found errors
Make sure you've activated the virtual environment and installed all dependencies:
```bash
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### Database errors
If you encounter database errors, you can reset the database by deleting `medipure.db` and restarting the application. It will be recreated automatically.

## Future Enhancements
- Video call integration
- Payment gateway integration
- Email/SMS notifications
- Prescription management
- Medical records storage
- Doctor ratings and reviews
- Advanced analytics dashboard
- Multi-language support

## License
© 2026 Medipure. All rights reserved.

## Support
For support, please visit the contact page or email support@medipure.com
