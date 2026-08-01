#!/usr/bin/env python3
"""
Paean Seed Data — 12 realistic Ontario patients + 1 admin doctor account.

All patients now include:
- city + province (required for DTC Part A)
- Disability checkmark booleans (patient intake — enables ~80% DTC auto-fill)
- yearImpaired (when condition started)
- devicesTherapy (walking aids, therapy — simple text from patient)

Run: python3 seedData.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import createApp
from app.database import db
from app.models import Patient, User, Clinic

patients = [
    {
        "patientName": "John Doe",
        "dateOfBirth": "1985-03-15",
        "healthCardNumber": "1234 567 890",
        "phn": "987654321",
        "address": "145 King Street, Toronto, ON M5H 1J8",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5H 1J8",
        "phoneNumber": "416-555-0199",
        "email": "john.doe@example.com",
        "sin": "123-456-789",
        "diagnosis": "Acute gastroenteritis with dehydration",
        "medications": "Ondansetron 4mg PRN",
        "allergies": "Penicillin",
        "notes": "Presented with severe nausea, vomiting, diarrhea for 2 days. Dehydrated on exam. Recommend rest and fluids for 3 days. Expected return to work Monday.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2026, "devicesTherapy": "None",
    },
    {
        "patientName": "Jane Smith",
        "dateOfBirth": "1962-04-15",
        "healthCardNumber": "9876 543 210",
        "phn": "123456789",
        "address": "789 Bloor Street, Toronto, ON M6G 1K7",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M6G 1K7",
        "phoneNumber": "416-555-0288",
        "email": "jane.smith@example.com",
        "sin": "987-654-321",
        "diagnosis": "Severe osteoarthritis of bilateral knees with chronic pain limiting mobility",
        "medications": "Celecoxib 200mg BID, Acetaminophen 1g QID",
        "allergies": "Sulfa drugs",
        "notes": "Marked difficulty walking more than 50 meters without rest. Unable to climb stairs without significant pain. Requires assistance with bathing and dressing on bad days. Total knee replacement recommended but delayed due to surgical wait list (estimated 14 months). Condition is prolonged and expected to last 12+ months.",
        "disabilityWalking": True, "disabilityDressing": True, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2019, "devicesTherapy": "Cane for walking, physiotherapy 2x/week",
    },
    {
        "patientName": "Michael Chen",
        "dateOfBirth": "1978-11-22",
        "healthCardNumber": "4567 891 234",
        "phn": "456789123",
        "address": "33 College Street, Toronto, ON M5T 3A1",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5T 3A1",
        "phoneNumber": "647-555-0344",
        "email": "michael.chen@example.com",
        "sin": "456-789-012",
        "diagnosis": "Essential hypertension (I10), Type 2 diabetes mellitus (E11.9)",
        "medications": "Lisinopril 20mg daily, Metformin 1000mg BID, Atorvastatin 40mg HS",
        "allergies": "None known",
        "notes": "BP trending down with lisinopril. Last A1C 7.2%, down from 8.1% three months ago. Diet and exercise counseling reinforced. Continue current regimen. Follow-up in 3 months for repeat labs.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2015, "devicesTherapy": "None",
    },
    {
        "patientName": "Sarah Johnson",
        "dateOfBirth": "1992-07-08",
        "healthCardNumber": "7891 234 567",
        "phn": "789123456",
        "address": "210 Yonge Street, Toronto, ON M5B 2L9",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5B 2L9",
        "phoneNumber": "416-555-0466",
        "email": "sarah.johnson@example.com",
        "sin": "789-012-345",
        "diagnosis": "Chronic migraine without aura (G43.709)",
        "medications": "Sumatriptan 50mg PRN, Propranolol 40mg BID",
        "allergies": "Codeine",
        "notes": "Migraine frequency reduced from 8/month to 3/month on propranolol. Triggers: stress, lack of sleep, red wine. Patient reports significant improvement. Continue prophylaxis. Consider Botox if frequency increases again.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2020, "devicesTherapy": "None",
    },
    {
        "patientName": "Robert Williams",
        "dateOfBirth": "1955-01-30",
        "healthCardNumber": "3456 789 012",
        "phn": "345678901",
        "address": "55 Spadina Avenue, Toronto, ON M5V 2J8",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5V 2J8",
        "phoneNumber": "416-555-0577",
        "email": "robert.williams@example.com",
        "sin": "345-678-901",
        "diagnosis": "COPD — severe (GOLD Stage III), FEV1 38% predicted",
        "medications": "Tiotropium 18mcg daily, Salmeterol/Fluticasone 50/500 BID, Albuterol PRN",
        "allergies": "None known",
        "notes": "Chronic dyspnea on exertion. 02 sat 92% room air. Ex-smoker (40 pack-years, quit 2019). No recent exacerbations. Pulmonary rehab completed. On maximal inhaled therapy. Consider long-term oxygen therapy if sats drop below 88%.",
        "disabilityWalking": True, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": True,
        "yearImpaired": 2018, "devicesTherapy": "Home oxygen therapy, inhalers",
    },
    {
        "patientName": "Emily Davis",
        "dateOfBirth": "1995-09-14",
        "healthCardNumber": "6789 012 345",
        "phn": "678901234",
        "address": "440 Bathurst Street, Toronto, ON M5T 2S6",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5T 2S6",
        "phoneNumber": "416-555-0688",
        "email": "emily.davis@example.com",
        "sin": "678-901-234",
        "diagnosis": "Generalized anxiety disorder (F41.1), mild",
        "medications": "Sertraline 50mg daily",
        "allergies": "None known",
        "notes": "Patient responding well to sertraline. GAD-7 score down from 14 to 7. Sleep improved. CBT referral made and patient attending sessions. Continue current dose. Follow-up in 6 weeks.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": True,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2023, "devicesTherapy": "CBT sessions weekly",
    },
    {
        "patientName": "David Brown",
        "dateOfBirth": "1970-05-20",
        "healthCardNumber": "2345 678 901",
        "phn": "234567890",
        "address": "12 Queen Street East, Toronto, ON M5C 1S6",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5C 1S6",
        "phoneNumber": "416-555-0799",
        "email": "david.brown@example.com",
        "sin": "234-567-890",
        "diagnosis": "Acute lower back pain — mechanical (M54.5), no red flags",
        "medications": "Naproxen 500mg BID, Cyclobenzaprine 10mg HS",
        "allergies": "Aspirin",
        "notes": "Onset 3 days ago after heavy lifting. No radicular symptoms. Negative straight leg raise. Normal neuro exam. Prescribed NSAIDs + muscle relaxant. Recommend rest 48h, then gradual return to activity. Physio referral given. Expected recovery 2-4 weeks.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2026, "devicesTherapy": "Physio referral given",
    },
    {
        "patientName": "Maria Garcia",
        "dateOfBirth": "1988-12-03",
        "healthCardNumber": "8901 234 567",
        "phn": "890123456",
        "address": "67 College Street, Toronto, ON M5T 1P5",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5T 1P5",
        "phoneNumber": "647-555-0810",
        "email": "maria.garcia@example.com",
        "sin": "890-123-456",
        "diagnosis": "Asthma — moderate persistent (J45.40)",
        "medications": "Budesonide/Formoterol 160/4.5 BID, Salbutamol PRN, Montelukast 10mg HS",
        "allergies": "Latex",
        "notes": "Asthma well-controlled on current regimen. Uses reliever <2x/week. No nighttime awakenings. No exacerbations in past 6 months. Spirometry stable. Continue current therapy. Annual flu shot administered.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2010, "devicesTherapy": "Inhalers",
    },
    {
        "patientName": "James Wilson",
        "dateOfBirth": "1965-08-17",
        "healthCardNumber": "5678 901 234",
        "phn": "567890123",
        "address": "88 Avenue Road, Toronto, ON M5R 2G4",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5R 2G4",
        "phoneNumber": "416-555-0922",
        "email": "james.wilson@example.com",
        "sin": "567-890-123",
        "diagnosis": "Acute myocardial infarction (STEMI) — 6 months post-stent",
        "medications": "Aspirin 81mg daily, Clopidogrel 75mg daily, Bisoprolol 5mg daily, Atorvastatin 80mg HS, Ramipril 10mg daily",
        "allergies": "None known",
        "notes": "6 months post-STEMI with DES to LAD. Cardiac rehab completed. Ejection fraction 52%. Lipids: LDL 1.6 mmol/L. Tolerating dual antiplatelet therapy well. Clopidogrel to continue for 12 months total. Follow-up echocardiogram in 6 months.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2025, "devicesTherapy": "Cardiac rehab completed",
    },
    {
        "patientName": "Patricia Taylor",
        "dateOfBirth": "1972-03-25",
        "healthCardNumber": "1234 567 890",
        "phn": "123456780",
        "address": "34 Bay Street, Toronto, ON M5J 2L2",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5J 2L2",
        "phoneNumber": "416-555-1033",
        "email": "patricia.taylor@example.com",
        "sin": "123-456-788",
        "diagnosis": "Primary hypothyroidism (E03.9) — Hashimoto's thyroiditis",
        "medications": "Levothyroxine 100mcg daily",
        "allergies": "None known",
        "notes": "TSH normalized from 12.4 to 2.1 mIU/L. Free T4 normal. Patient reports improved energy. Weight stable. Continue current levothyroxine dose. Recheck TSH in 6 months. Bone density scan recommended due to family history of osteoporosis.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2018, "devicesTherapy": "None",
    },
    {
        "patientName": "Ahmed Hassan",
        "dateOfBirth": "1980-06-10",
        "healthCardNumber": "4567 890 123",
        "phn": "456890127",
        "address": "99 King Street West, Toronto, ON M5X 1A9",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5X 1A9",
        "phoneNumber": "647-555-1144",
        "email": "ahmed.hassan@example.com",
        "sin": "456-890-136",
        "diagnosis": "Irritable bowel syndrome — diarrhea-predominant (K58.0)",
        "medications": "Loperamide 2mg PRN, Rifaximin 550mg TID x 14 days",
        "allergies": "Erythromycin",
        "notes": "IBS-D symptoms improved after rifaximin course. Stool frequency reduced from 6/day to 2-3/day. No alarm features. Fecal calprotectin normal. Low FODMAP diet counseling given. Loperamide for breakthrough symptoms. Follow-up PRN.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2019, "devicesTherapy": "None",
    },
    {
        "patientName": "Lisa Anderson",
        "dateOfBirth": "1990-02-18",
        "healthCardNumber": "7890 123 456",
        "phn": "789012347",
        "address": "77 Adelaide Street, Toronto, ON M5C 1S9",
        "city": "Toronto",
        "province": "Ontario",
        "postalCode": "M5C 1S9",
        "phoneNumber": "416-555-1255",
        "email": "lisa.anderson@example.com",
        "sin": "789-123-458",
        "diagnosis": "Iron deficiency anemia (D50.9) — investigation underway",
        "medications": "Ferrous sulfate 325mg BID with vitamin C",
        "allergies": "None known",
        "notes": "Hemoglobin 102 g/L, ferritin 8 ug/L. Menstrual history significant for heavy periods. GI workup initiated — fecal immunochemical test negative. Gynecology referral made for menorrhagia. Iron supplementation started. Recheck CBC in 4 weeks.",
        "disabilityWalking": False, "disabilityDressing": False, "disabilityFeeding": False,
        "disabilitySpeaking": False, "disabilityHearing": False, "disabilityVision": False,
        "disabilityEliminating": False, "disabilityMental": False,
        "disabilityIndependentLiving": False, "disabilityTherapy": False,
        "yearImpaired": 2026, "devicesTherapy": "Iron supplements",
    },
]


def seed():
    print("=== Paean Seed Data ===\n")

    app = createApp()

    with app.app_context():
        # Create or find demo clinic
        clinic = Clinic.query.filter_by(name="Paean Demo Clinic").first()
        if not clinic:
            clinic = Clinic(
                name="Paean Demo Clinic",
                address="100 Yonge Street, Toronto, ON M5B 2L9",
                phoneNumber="416-555-0000",
                email="demo@paean.ca",
            )
            db.session.add(clinic)
            db.session.flush()
            print(f"✓ Created clinic: {clinic.name}")

        # Create or find Doctor Doctor account (the user's account)
        doctorEmail = "doctor@doctor.com"
        doctor = User.query.filter_by(email=doctorEmail).first()
        if not doctor:
            doctor = User(
                email=doctorEmail,
                role="doctor",
                firstName="Doctor",
                lastName="Doctor",
                licenseNumber="CPSO-99999",
                specialty="Family Medicine",
                clinicId=clinic.id if clinic else None,
                isActive=True,
            )
            doctor.setPassword("Doctor123!")
            db.session.add(doctor)
            db.session.flush()
            print(f"✓ Created doctor account: {doctorEmail} (password: Doctor123!)")
        else:
            if not doctor.clinicId and clinic:
                doctor.clinicId = clinic.id
            print(f"  Doctor account exists: {doctorEmail} (id={doctor.id})")

        # Also ensure admin account exists
        adminEmail = "admin@paean.ca"
        admin = User.query.filter_by(email=adminEmail).first()
        if not admin:
            admin = User(
                email=adminEmail,
                role="admin",
                firstName="Admin",
                lastName="Doctor",
                licenseNumber="CPSO-00000",
                specialty="Internal Medicine",
                clinicId=clinic.id if clinic else None,
                isActive=True,
            )
            admin.setPassword("Admin12345!")
            db.session.add(admin)
            print(f"✓ Created admin doctor: {adminEmail} (password: Admin12345!)")
        else:
            print(f"  Admin doctor exists: {adminEmail}")

        # Create patients — ALL linked to Doctor Doctor's account
        created = 0
        updated = 0
        for p in patients:
            existing = Patient.query.filter_by(
                patientName=p["patientName"],
                dateOfBirth=p["dateOfBirth"],
            ).first()

            if existing:
                for key, val in p.items():
                    setattr(existing, key, val)
                existing.primaryPhysicianId = doctor.id
                updated += 1
            else:
                patient = Patient(**p)
                patient.primaryPhysicianId = doctor.id
                db.session.add(patient)
                created += 1

        db.session.commit()

        totalPatients = Patient.query.count()
        totalUsers = User.query.count()
        totalClinics = Clinic.query.count()

        print(f"\n✓ Created {created} new patients, updated {updated} existing")
        print(f"\nDatabase totals:")
        print(f"  Patients: {totalPatients}")
        print(f"  Users:    {totalUsers}")
        print(f"  Clinics:  {totalClinics}")

        print(f"\n=== Seed Complete ===")
        print(f"  Admin login: admin@paean.ca / Admin12345!")


if __name__ == "__main__":
    seed()
