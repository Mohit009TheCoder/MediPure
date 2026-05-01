"""
Seed database with top-rated doctors with realistic profiles
"""
import database
import auth

# Sample top doctors data
TOP_DOCTORS = [
    {
        "email": "dr.sarah.johnson@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. Sarah Johnson",
        "role": "doctor",
        "phone": "+1 (555) 123-4567",
        "address": "456 Medical Plaza, Suite 200",
        "city": "New York",
        "zip": "10001",
        "area": "Manhattan",
        "license_number": "NY-MD-45678",
        "specialty": "Cardiologist",
        "qualification": "MD, FACC, FSCAI",
        "experience": 15,
        "clinic_name": "Heart Care Center of New York",
        "consultation_fee": 350,
        "bio": "Board-certified cardiologist with 15+ years of experience in interventional cardiology. Specialized in treating complex heart conditions with minimally invasive procedures.",
        "total_patients_treated": 3500,
        "patients_cured": 3200,
        "success_rate": 91,
        "rating": 48,  # 4.8 out of 5
        "total_reviews": 450,
        "awards": "Best Cardiologist Award 2024,Top Doctor NYC 2023,Excellence in Patient Care 2022",
        "certifications": "American Board of Internal Medicine,Interventional Cardiology Certification,Advanced Cardiac Life Support",
        "languages": "English,Spanish,French",
        "education": "Harvard Medical School (MD), Johns Hopkins Hospital (Residency), Cleveland Clinic (Fellowship in Interventional Cardiology)"
    },
    {
        "email": "dr.michael.chen@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. Michael Chen",
        "role": "doctor",
        "phone": "+1 (555) 234-5678",
        "address": "789 Neurology Center, 5th Floor",
        "city": "New York",
        "zip": "10002",
        "area": "Brooklyn",
        "license_number": "NY-MD-56789",
        "specialty": "Neurologist",
        "qualification": "MD, PhD, FAAN",
        "experience": 18,
        "clinic_name": "Advanced Neurology Institute",
        "consultation_fee": 400,
        "bio": "Leading neurologist specializing in stroke treatment, epilepsy, and neurodegenerative diseases. Published over 50 research papers in top medical journals.",
        "total_patients_treated": 4200,
        "patients_cured": 3800,
        "success_rate": 90,
        "rating": 49,  # 4.9 out of 5
        "total_reviews": 520,
        "awards": "Neurologist of the Year 2024,Research Excellence Award 2023,Patient Choice Award 2022,Top 10 Neurologists in America",
        "certifications": "American Board of Psychiatry and Neurology,Epilepsy Specialist Certification,Stroke Intervention Certification",
        "languages": "English,Mandarin,Cantonese",
        "education": "Stanford Medical School (MD, PhD), Massachusetts General Hospital (Residency), Mayo Clinic (Fellowship in Neurology)"
    },
    {
        "email": "dr.emily.rodriguez@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. Emily Rodriguez",
        "role": "doctor",
        "phone": "+1 (555) 345-6789",
        "address": "321 Pediatric Care Building",
        "city": "New York",
        "zip": "10003",
        "area": "Queens",
        "license_number": "NY-MD-67890",
        "specialty": "Pediatrician",
        "qualification": "MD, FAAP",
        "experience": 12,
        "clinic_name": "Children's Health & Wellness Center",
        "consultation_fee": 250,
        "bio": "Compassionate pediatrician dedicated to providing comprehensive care for children from newborns to adolescents. Specialized in childhood development and preventive care.",
        "total_patients_treated": 5600,
        "patients_cured": 5400,
        "success_rate": 96,
        "rating": 50,  # 5.0 out of 5
        "total_reviews": 680,
        "awards": "Best Pediatrician NYC 2024,Parents' Choice Award 2023,Excellence in Child Care 2022",
        "certifications": "American Board of Pediatrics,Pediatric Advanced Life Support,Neonatal Resuscitation Program",
        "languages": "English,Spanish,Portuguese",
        "education": "Columbia University Medical School (MD), Children's Hospital of Philadelphia (Residency), Boston Children's Hospital (Fellowship)"
    },
    {
        "email": "dr.james.williams@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. James Williams",
        "role": "doctor",
        "phone": "+1 (555) 456-7890",
        "address": "555 Orthopedic Center, 3rd Floor",
        "city": "New York",
        "zip": "10004",
        "area": "Manhattan",
        "license_number": "NY-MD-78901",
        "specialty": "Orthopedic",
        "qualification": "MD, FAAOS",
        "experience": 20,
        "clinic_name": "Elite Orthopedic & Sports Medicine",
        "consultation_fee": 380,
        "bio": "Renowned orthopedic surgeon with expertise in joint replacement, sports injuries, and minimally invasive spine surgery. Team physician for professional athletes.",
        "total_patients_treated": 3800,
        "patients_cured": 3500,
        "success_rate": 92,
        "rating": 47,  # 4.7 out of 5
        "total_reviews": 410,
        "awards": "Top Orthopedic Surgeon 2024,Sports Medicine Excellence Award 2023,Innovation in Surgery Award 2022",
        "certifications": "American Board of Orthopedic Surgery,Sports Medicine Certification,Arthroscopic Surgery Specialist",
        "languages": "English,German",
        "education": "Yale School of Medicine (MD), Hospital for Special Surgery (Residency), Andrews Sports Medicine (Fellowship)"
    },
    {
        "email": "dr.priya.patel@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. Priya Patel",
        "role": "doctor",
        "phone": "+1 (555) 567-8901",
        "address": "888 Dermatology Clinic, Suite 100",
        "city": "New York",
        "zip": "10005",
        "area": "Manhattan",
        "license_number": "NY-MD-89012",
        "specialty": "Dermatologist",
        "qualification": "MD, FAAD",
        "experience": 14,
        "clinic_name": "Advanced Skin & Laser Center",
        "consultation_fee": 300,
        "bio": "Expert dermatologist specializing in medical and cosmetic dermatology. Pioneer in laser treatments and advanced skin cancer detection techniques.",
        "total_patients_treated": 6200,
        "patients_cured": 5900,
        "success_rate": 95,
        "rating": 48,  # 4.8 out of 5
        "total_reviews": 590,
        "awards": "Best Dermatologist NYC 2024,Innovation in Dermatology 2023,Patient Satisfaction Award 2022",
        "certifications": "American Board of Dermatology,Mohs Surgery Certification,Cosmetic Dermatology Specialist",
        "languages": "English,Hindi,Gujarati",
        "education": "NYU School of Medicine (MD), Mount Sinai Hospital (Residency), Memorial Sloan Kettering (Fellowship in Dermatologic Oncology)"
    },
    {
        "email": "dr.robert.anderson@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. Robert Anderson",
        "role": "doctor",
        "phone": "+1 (555) 678-9012",
        "address": "999 Psychiatry Associates, 7th Floor",
        "city": "New York",
        "zip": "10006",
        "area": "Brooklyn",
        "license_number": "NY-MD-90123",
        "specialty": "Psychiatrist",
        "qualification": "MD, PhD",
        "experience": 16,
        "clinic_name": "Mind & Wellness Psychiatric Center",
        "consultation_fee": 320,
        "bio": "Compassionate psychiatrist with dual training in medicine and psychology. Specialized in treating anxiety, depression, and trauma-related disorders using evidence-based approaches.",
        "total_patients_treated": 2800,
        "patients_cured": 2500,
        "success_rate": 89,
        "rating": 47,  # 4.7 out of 5
        "total_reviews": 380,
        "awards": "Excellence in Mental Health Care 2024,Top Psychiatrist Award 2023,Compassionate Doctor Award 2022",
        "certifications": "American Board of Psychiatry and Neurology,Addiction Medicine Certification,Psychopharmacology Specialist",
        "languages": "English,Italian",
        "education": "University of Pennsylvania Medical School (MD, PhD), McLean Hospital (Residency), National Institute of Mental Health (Research Fellowship)"
    },
    {
        "email": "dr.lisa.thompson@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. Lisa Thompson",
        "role": "doctor",
        "phone": "+1 (555) 789-0123",
        "address": "222 Women's Health Center",
        "city": "New York",
        "zip": "10007",
        "area": "Queens",
        "license_number": "NY-MD-01234",
        "specialty": "Gynecologist",
        "qualification": "MD, FACOG",
        "experience": 13,
        "clinic_name": "Women's Wellness & Maternity Care",
        "consultation_fee": 280,
        "bio": "Dedicated OB-GYN providing comprehensive women's healthcare from adolescence through menopause. Specialized in high-risk pregnancies and minimally invasive gynecologic surgery.",
        "total_patients_treated": 4500,
        "patients_cured": 4300,
        "success_rate": 95,
        "rating": 49,  # 4.9 out of 5
        "total_reviews": 510,
        "awards": "Best OB-GYN NYC 2024,Women's Health Champion 2023,Excellence in Maternal Care 2022",
        "certifications": "American Board of Obstetrics and Gynecology,Maternal-Fetal Medicine,Robotic Surgery Certification",
        "languages": "English,Spanish",
        "education": "Cornell Medical School (MD), New York-Presbyterian Hospital (Residency), Columbia University (Fellowship in Maternal-Fetal Medicine)"
    },
    {
        "email": "dr.david.kim@medipure.com",
        "password": "doctor123",
        "full_name": "Dr. David Kim",
        "role": "doctor",
        "phone": "+1 (555) 890-1234",
        "address": "444 Eye Care Institute, 2nd Floor",
        "city": "New York",
        "zip": "10008",
        "area": "Manhattan",
        "license_number": "NY-MD-12345",
        "specialty": "Ophthalmologist",
        "qualification": "MD, FACS",
        "experience": 17,
        "clinic_name": "Vision Excellence Eye Center",
        "consultation_fee": 340,
        "bio": "Leading ophthalmologist and eye surgeon specializing in cataract surgery, LASIK, and treatment of retinal diseases. Performed over 5,000 successful eye surgeries.",
        "total_patients_treated": 5200,
        "patients_cured": 4900,
        "success_rate": 94,
        "rating": 48,  # 4.8 out of 5
        "total_reviews": 470,
        "awards": "Top Ophthalmologist 2024,Excellence in Eye Surgery 2023,Innovation in Vision Care 2022",
        "certifications": "American Board of Ophthalmology,Retina Specialist Certification,Refractive Surgery Certification",
        "languages": "English,Korean,Japanese",
        "education": "Duke University School of Medicine (MD), Wills Eye Hospital (Residency), Bascom Palmer Eye Institute (Fellowship in Vitreoretinal Surgery)"
    }
]

def seed_database():
    """Seed database with top doctors"""
    db = database.SessionLocal()
    
    try:
        print("🌱 Seeding database with top-rated doctors...")
        
        for doctor_data in TOP_DOCTORS:
            # Check if doctor already exists
            existing = db.query(database.User).filter(
                database.User.email == doctor_data["email"]
            ).first()
            
            if existing:
                print(f"⏭️  Skipping {doctor_data['full_name']} - already exists")
                continue
            
            # Hash password
            hashed_pwd = auth.get_password_hash(doctor_data["password"])
            
            # Create doctor
            doctor = database.User(
                email=doctor_data["email"],
                hashed_password=hashed_pwd,
                full_name=doctor_data["full_name"],
                role=doctor_data["role"],
                phone=doctor_data["phone"],
                address=doctor_data["address"],
                city=doctor_data["city"],
                zip=doctor_data["zip"],
                area=doctor_data["area"],
                license_number=doctor_data["license_number"],
                specialty=doctor_data["specialty"],
                qualification=doctor_data["qualification"],
                experience=doctor_data["experience"],
                clinic_name=doctor_data["clinic_name"],
                consultation_fee=doctor_data["consultation_fee"],
                bio=doctor_data["bio"],
                total_patients_treated=doctor_data["total_patients_treated"],
                patients_cured=doctor_data["patients_cured"],
                success_rate=doctor_data["success_rate"],
                rating=doctor_data["rating"],
                total_reviews=doctor_data["total_reviews"],
                awards=doctor_data["awards"],
                certifications=doctor_data["certifications"],
                languages=doctor_data["languages"],
                education=doctor_data["education"]
            )
            
            db.add(doctor)
            print(f"✅ Added {doctor_data['full_name']} - {doctor_data['specialty']}")
        
        db.commit()
        print(f"\n🎉 Successfully seeded {len(TOP_DOCTORS)} top-rated doctors!")
        print("\n📊 Doctor Statistics:")
        print(f"   Total Doctors: {len(TOP_DOCTORS)}")
        print(f"   Average Success Rate: {sum(d['success_rate'] for d in TOP_DOCTORS) / len(TOP_DOCTORS):.1f}%")
        print(f"   Total Patients Treated: {sum(d['total_patients_treated'] for d in TOP_DOCTORS):,}")
        print(f"   Total Patients Cured: {sum(d['patients_cured'] for d in TOP_DOCTORS):,}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
