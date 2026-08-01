"""
Database models for Paean.

All PII fields use EncryptedField — encrypted individually at rest.
AuditLog is append-only — no updates or deletes allowed.
"""

import json
import bcrypt
from datetime import datetime, timezone
from app.database import db
from app.encryption import EncryptedField


class Patient(db.Model):
    """Patient record — all PII fields encrypted at field level."""
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    primaryPhysicianId = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    patientName = db.Column(EncryptedField(), nullable=False)
    dateOfBirth = db.Column(EncryptedField())
    healthCardNumber = db.Column(EncryptedField())
    phn = db.Column(EncryptedField())  # Provincial Health Number
    address = db.Column(EncryptedField())
    city = db.Column(EncryptedField())  # Required — for DTC Part A
    province = db.Column(EncryptedField())  # Required — for DTC Part A
    postalCode = db.Column(EncryptedField())
    phoneNumber = db.Column(EncryptedField())
    email = db.Column(EncryptedField())
    sin = db.Column(EncryptedField())
    diagnosis = db.Column(EncryptedField())
    medications = db.Column(EncryptedField())
    allergies = db.Column(EncryptedField())
    notes = db.Column(EncryptedField())

    # Disability intake fields — boolean checkmarks patient provides at intake
    # These enable ~80% auto-fill of DTC T2201 form
    disabilityWalking = db.Column(db.Boolean, default=False)  # Difficulty walking 50m+
    disabilityDressing = db.Column(db.Boolean, default=False)  # Difficulty dressing
    disabilityFeeding = db.Column(db.Boolean, default=False)  # Difficulty feeding
    disabilitySpeaking = db.Column(db.Boolean, default=False)  # Difficulty speaking
    disabilityHearing = db.Column(db.Boolean, default=False)  # Difficulty hearing
    disabilityVision = db.Column(db.Boolean, default=False)  # Vision impairment
    disabilityEliminating = db.Column(db.Boolean, default=False)  # Bowel/bladder management
    disabilityMental = db.Column(db.Boolean, default=False)  # Mental function impairment
    disabilityIndependentLiving = db.Column(db.Boolean, default=False)  # Needs daily help to live
    disabilityTherapy = db.Column(db.Boolean, default=False)  # Receives life-sustaining therapy
    yearImpaired = db.Column(db.Integer, nullable=True)  # Year condition started
    devicesTherapy = db.Column(EncryptedField())  # "I use a cane", "I do physio" — simple text

    createdAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updatedAt = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    def toDict(self, includePii: bool = False):
        """Serialize patient. PII only included if explicitly requested."""
        data = {"id": self.id, "primaryPhysicianId": self.primaryPhysicianId, "createdAt": str(self.createdAt)}
        if includePii:
            data.update({
                "patientName": self.patientName,
                "dateOfBirth": self.dateOfBirth,
                "healthCardNumber": self.healthCardNumber,
                "address": self.address,
                "city": self.city,
                "province": self.province,
                "postalCode": self.postalCode,
                "sin": self.sin,
                "diagnosis": self.diagnosis,
                "medications": self.medications,
                "allergies": self.allergies,
                "notes": self.notes,
                "disabilityWalking": self.disabilityWalking,
                "disabilityDressing": self.disabilityDressing,
                "disabilityFeeding": self.disabilityFeeding,
                "disabilitySpeaking": self.disabilitySpeaking,
                "disabilityHearing": self.disabilityHearing,
                "disabilityVision": self.disabilityVision,
                "disabilityEliminating": self.disabilityEliminating,
                "disabilityMental": self.disabilityMental,
                "disabilityIndependentLiving": self.disabilityIndependentLiving,
                "disabilityTherapy": self.disabilityTherapy,
                "yearImpaired": self.yearImpaired,
                "devicesTherapy": self.devicesTherapy,
            })
        return data


class Appointment(db.Model):
    """Appointment records — doctor writes clinical note, AI extracts patient field updates."""
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patientId = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    physicianId = db.Column(db.String(100))  # From JWT identity
    appointmentDate = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    clinicalNote = db.Column(EncryptedField())  # Doctor's free-text note
    aiSummary = db.Column(db.Text)  # LLM-generated summary of the visit
    fieldUpdates = db.Column(db.Text)  # JSON of fields the AI extracted/updated
    status = db.Column(db.String(50), default="completed")  # completed, reviewed

    createdAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def toDict(self):
        return {
            "id": self.id,
            "patientId": self.patientId,
            "physicianId": self.physicianId,
            "appointmentDate": str(self.appointmentDate) if self.appointmentDate else None,
            "clinicalNote": self.clinicalNote,
            "aiSummary": self.aiSummary,
            "fieldUpdates": json.loads(self.fieldUpdates) if self.fieldUpdates else None,
            "status": self.status,
            "createdAt": str(self.createdAt),
        }


class FormSubmission(db.Model):
    """Tracks each form submission through the pipeline."""
    __tablename__ = "formSubmissions"

    id = db.Column(db.Integer, primary_key=True)
    formType = db.Column(db.String(50), nullable=False)  # dtc, insurance, cpp
    patientId = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    physicianId = db.Column(db.String(100))
    status = db.Column(db.String(50), default="draft")  # draft, scanned, submitted

    # PII compliance scan results
    piiScanPassed = db.Column(db.Boolean, default=False)
    piiFindings = db.Column(db.Text)  # JSON string of scan results
    redactedPreview = db.Column(db.Text)  # Token-redacted version

    # The final form data (encrypted)
    formData = db.Column(EncryptedField())

    createdAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    submittedAt = db.Column(db.DateTime)

    def toDict(self):
        return {
            "id": self.id,
            "formType": self.formType,
            "patientId": self.patientId,
            "physicianId": self.physicianId,
            "status": self.status,
            "piiScanPassed": self.piiScanPassed,
            "piiFindings": self.piiFindings,
            "createdAt": str(self.createdAt),
            "submittedAt": str(self.submittedAt) if self.submittedAt else None,
        }


class AuditLog(db.Model):
    """
    Immutable audit trail — every PII access logged.

    PHIPA Requirement: Health information custodians must log all
    access to electronic health records.
    """
    __tablename__ = "auditLogs"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    piiFields = db.Column(db.Text)
    endpoint = db.Column(db.String(200))
    patientId = db.Column(db.String(100))
    ipAddress = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, nullable=False)

    def toDict(self):
        import json
        return {
            "id": self.id,
            "userId": self.userId,
            "action": self.action,
            "piiFields": json.loads(self.piiFields) if self.piiFields else [],
            "endpoint": self.endpoint,
            "patientId": self.patientId,
            "ipAddress": self.ipAddress,
            "timestamp": str(self.timestamp),
        }


class Clinic(db.Model):
    """Clinic/organization that doctors belong to."""
    __tablename__ = "clinics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(EncryptedField())
    phoneNumber = db.Column(EncryptedField())
    email = db.Column(EncryptedField())
    createdAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "phoneNumber": self.phoneNumber,
            "email": self.email,
            "createdAt": str(self.createdAt),
        }


class User(db.Model):
    """Base user model for auth. Roles: doctor, patient, admin."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    passwordHash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="doctor")
    firstName = db.Column(EncryptedField())
    lastName = db.Column(EncryptedField())
    isActive = db.Column(db.Boolean, default=True)
    isVerified = db.Column(db.Boolean, default=False)
    clinicId = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=True)

    # Doctor-specific fields (null for patients)
    licenseNumber = db.Column(EncryptedField())
    specialty = db.Column(db.String(100), nullable=True)

    createdAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updatedAt = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    def setPassword(self, password: str):
        self.passwordHash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def checkPassword(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.passwordHash.encode("utf-8")
        )

    def toDict(self, includePii: bool = False):
        data = {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "isActive": self.isActive,
            "isVerified": self.isVerified,
            "clinicId": self.clinicId,
            "createdAt": str(self.createdAt),
        }
        if includePii:
            data.update({
                "firstName": self.firstName,
                "lastName": self.lastName,
                "licenseNumber": self.licenseNumber,
                "specialty": self.specialty,
            })
        return data
