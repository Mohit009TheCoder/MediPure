# Medipure - Doctor Appointment System

A comprehensive healthcare platform connecting patients with doctors through video and physical consultations, with integrated payment processing and earnings management.

## 🌟 Features

### For Patients
- 🔍 Search doctors by specialty and location
- 📅 Book video or physical consultations
- 💳 Secure payment via Razorpay
- 🧾 Digital payment receipts
- 🤖 AI-powered symptom analysis
- ⭐ View top-rated doctors
- 📱 Responsive mobile-friendly interface

### For Doctors
- 🕐 Manage appointment slots
- 📊 View earnings dashboard
- 💰 Track consultation revenue
- 💸 Request withdrawals to bank account
- 📜 View withdrawal history
- 👥 Manage patient appointments
- 📈 Real-time earnings updates

### For Admins
- 👨‍⚕️ Manage doctors and patients
- 📊 System analytics and statistics
- 💼 Process withdrawal requests
- 📋 View all appointments and receipts
- 🔍 Monitor platform activity

## 💰 Business Model

- **Platform Fee:** 20% of consultation fee
- **Doctor Earnings:** 80% of consultation fee
- **Automatic Calculation:** Real-time earnings updates
- **Withdrawal System:** 3-5 business days processing
- **Minimum Withdrawal:** ₹100

## 🚀 Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLite with SQLAlchemy
- **Frontend:** HTML5, CSS3, JavaScript
- **Payment:** Razorpay Integration
- **Authentication:** JWT (JSON Web Tokens)
- **Timezone:** IST (Indian Standard Time)

## 📦 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python main.py
```
Or use the start script:
```bash
bash start.sh
```

### 3. Access the Application
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 👥 Test Accounts

### Doctor Account
- **Email:** doctor@test.com
- **Password:** test123
- **Consultation Fee:** ₹500

### Patient Account
- **Email:** patient@test.com
- **Password:** test123

### Admin Account
- **Email:** admin@medipure.com
- **Password:** admin123

## 📚 Documentation

### Complete Guides
- **[EARNINGS_SYSTEM.md](EARNINGS_SYSTEM.md)** - Complete earnings & withdrawal system documentation
- **[TESTING_EARNINGS.md](TESTING_EARNINGS.md)** - Step-by-step testing guide
- **[UI_SCREENSHOTS_GUIDE.md](UI_SCREENSHOTS_GUIDE.md)** - Visual UI reference
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - High-level overview

### Quick Links
- **[System Overview](SYSTEM_OVERVIEW.txt)** - Architecture overview
- **[Navigation Fix](NAVIGATION_FIX.md)** - Smart home redirect feature

## 🧪 Testing

### Quick Test Flow
1. **Login as Patient** → Book appointment → Complete payment
2. **Login as Doctor** → View earnings → Request withdrawal
3. **Check withdrawal history** → Track status

See [TESTING_EARNINGS.md](TESTING_EARNINGS.md) for detailed testing instructions.

## 🎨 Key Features Implemented

### ✅ Payment System
- Razorpay integration
- Automatic receipt generation
- IST timezone support
- Payment verification

### ✅ Earnings Management
- Real-time earnings tracking
- 20/80 platform fee split
- Detailed breakdown by consultation
- Visual earnings dashboard

### ✅ Withdrawal System
- Bank account integration
- Minimum withdrawal validation
- Status tracking (pending/processing/completed/failed)
- Automatic balance updates
- Admin approval workflow

### ✅ Security
- JWT authentication
- Role-based access control
- Input validation
- Account number masking
- Secure payment processing

## 📱 Responsive Design

- ✅ Desktop (1024px+)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)
- ✅ Touch-friendly interface

## 🔐 Security Features

- JWT token authentication
- Password hashing (bcrypt)
- Role-based authorization
- Payment signature verification
- SQL injection prevention
- XSS protection

## 🌐 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /token` - Login

### Doctor Endpoints
- `GET /doctor/earnings` - Earnings summary
- `GET /doctor/earnings/breakdown` - Detailed breakdown
- `POST /doctor/withdraw` - Request withdrawal
- `GET /doctor/withdrawals` - Withdrawal history
- `POST /doctor/slots` - Add appointment slot
- `GET /doctor/slots` - View slots
- `GET /doctor/appointments` - View appointments

### Patient Endpoints
- `GET /doctors/search` - Search doctors
- `GET /doctors/{id}/slots` - View doctor slots
- `POST /appointments/create-order` - Create appointment
- `POST /appointments/verify-payment` - Verify payment
- `GET /patient/receipts` - View receipts

### Admin Endpoints
- `GET /admin/stats` - System statistics
- `GET /admin/withdrawals` - All withdrawals
- `PUT /admin/withdrawals/{id}` - Update withdrawal
- `GET /admin/doctors` - All doctors
- `GET /admin/patients` - All patients

## 🛠️ Development

### Project Structure
```
medipure/
├── main.py                 # FastAPI application
├── database.py            # Database models
├── auth.py                # Authentication
├── config.py              # Configuration
├── razorpay_config.py     # Payment config
├── static/                # Frontend files
│   ├── dashboard.html     # Main dashboard
│   ├── payment.html       # Payment page
│   ├── receipt.html       # Receipt page
│   └── ...
├── requirements.txt       # Python dependencies
└── medipure.db           # SQLite database
```

### Database Schema
- **Users** - Admin, doctors, patients
- **Slots** - Doctor availability
- **Appointments** - Bookings
- **PaymentReceipts** - Payment records
- **DoctorEarnings** - Earnings tracking
- **Withdrawals** - Withdrawal requests

## 🚀 Production Deployment

### Before Going Live
1. Update Razorpay keys (test → live)
2. Configure production database
3. Set up SSL/HTTPS
4. Configure email notifications
5. Set up monitoring and logging
6. Backup strategy

## 📊 System Status

- ✅ **Backend:** Complete and tested
- ✅ **Frontend:** Complete and responsive
- ✅ **Payment:** Razorpay integrated
- ✅ **Earnings:** Real-time tracking
- ✅ **Withdrawals:** Full workflow
- ✅ **Documentation:** Comprehensive

## 🎯 Future Enhancements

- [ ] Email notifications
- [ ] SMS alerts
- [ ] Video call integration
- [ ] Prescription management
- [ ] Medical records
- [ ] Analytics dashboard
- [ ] Mobile app
- [ ] Multi-language support

## 📞 Support

For issues or questions:
1. Check the documentation files
2. Review the testing guide
3. Check API documentation at `/docs`
4. Review code comments

## 📄 License

This project is for educational and demonstration purposes.

---

**Status:** ✅ Production-Ready
**Version:** 2.0
**Last Updated:** May 3, 2026

Built with ❤️ using FastAPI, Razorpay, and modern web technologies.
