"""
Disability Tax Credit (DTC) Form Schema.

The DTC is the #1 most burdensome form in Canada according to the CMA/CFIB
2026 report:
  - 53% of physicians rate it as a major burden
  - 32% rate it as a moderate burden
  - Average 36.6 minutes to complete
  - Completed 32.2 times per year per physician
  - Only 45.3% of physicians are compensated

This schema defines the form structure and maps which clinical data
fields are required, enabling Agent 2 to auto-populate from EMR data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ImpairmentType(str, Enum):
    vision = "vision"
    hearing = "hearing"
    mobility = "mobility"
    mentalFunctions = "mentalFunctions"
    feeding = "feeding"
    dressing = "dressing"
    lifeSustainingTherapy = "lifeSustainingTherapy"
    cumulativeEffect = "cumulativeEffect"


class DtcFormSection(BaseModel):
    """A section of the DTC form."""
    sectionId: str
    sectionName: str
    fields: List["DtcFormField"]


class DtcFormField(BaseModel):
    """A single field on the DTC form."""
    fieldId: str
    label: str
    fieldType: str  # text, date, checkbox, radio, textarea, number
    required: bool = True
    piiClassification: str  # What kind of PII this field contains
    emrSource: Optional[str] = None  # Which EMR field maps to this
    helpText: Optional[str] = None


# ─── DTC Form Schema Definition ────────────────────────────────────────

dtcFormSchema = {
    "formId": "dtc",
    "formName": "Disability Tax Credit Certificate (T2201)",
    "formNumber": "T2201",
    "issuingBody": "Canada Revenue Agency (CRA)",
    "averageCompletionTimeMin": 36.6,
    "averageAnnualCompletions": 32.2,
    "percentPhysiciansCompensated": 45.3,
    "percentMajorBurden": 53,
    "percentModerateBurden": 32,
    "sections": [
        {
            "sectionId": "sectionA",
            "sectionName": "Patient Information",
            "fields": [
                {
                    "fieldId": "patientName",
                    "label": "Full name of person with disability",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "patientName",
                    "emrSource": "patient.patientName",
                    "helpText": "Legal name as it appears on tax return",
                },
                {
                    "fieldId": "dateOfBirth",
                    "label": "Date of birth",
                    "fieldType": "date",
                    "required": True,
                    "piiClassification": "dateOfBirth",
                    "emrSource": "patient.dateOfBirth",
                },
                {
                    "fieldId": "sin",
                    "label": "Social Insurance Number",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "sin",
                    "emrSource": "patient.sin",
                },
                {
                    "fieldId": "address",
                    "label": "Mailing address",
                    "fieldType": "textarea",
                    "required": True,
                    "piiClassification": "address",
                    "emrSource": "patient.address",
                },
                {
                    "fieldId": "phoneNumber",
                    "label": "Phone number",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "phoneNumber",
                    "emrSource": "patient.phoneNumber",
                },
            ],
        },
        {
            "sectionId": "sectionB",
            "sectionName": "Certification of Disability",
            "fields": [
                {
                    "fieldId": "impairmentType",
                    "label": "Type of impairment",
                    "fieldType": "checkbox",
                    "required": True,
                    "piiClassification": "diagnosis",
                    "emrSource": "patient.diagnosis",
                    "helpText": "Check all that apply",
                },
                {
                    "fieldId": "onsetDate",
                    "label": "When did the impairment begin?",
                    "fieldType": "date",
                    "required": True,
                    "piiClassification": "diagnosis",
                    "emrSource": "patient.diagnosisOnsetDate",
                },
                {
                    "fieldId": "effectsDescription",
                    "label": "Describe the effects of the impairment on daily activities",
                    "fieldType": "textarea",
                    "required": True,
                    "piiClassification": "notes",
                    "emrSource": "patient.clinicalNotes",
                    "helpText": "Be specific about limitations in daily living",
                },
                {
                    "fieldId": "duration",
                    "label": "Expected duration of impairment",
                    "fieldType": "radio",
                    "required": True,
                    "piiClassification": "notes",
                    "emrSource": "patient.prognosis",
                    "helpText": "Prolonged = 12+ months continuous",
                },
                {
                    "fieldId": "lifeSustainingTherapy",
                    "label": "Does the patient require life-sustaining therapy?",
                    "fieldType": "radio",
                    "required": True,
                    "piiClassification": "medications",
                    "emrSource": "patient.treatmentPlan",
                },
                {
                    "fieldId": "therapyFrequency",
                    "label": "Therapy frequency (times per week)",
                    "fieldType": "number",
                    "required": False,
                    "piiClassification": "medications",
                    "emrSource": "patient.treatmentPlan",
                },
            ],
        },
        {
            "sectionId": "sectionC",
            "sectionName": "Medical Practitioner Information",
            "fields": [
                {
                    "fieldId": "physicianName",
                    "label": "Medical practitioner name",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "physicianName",
                    "emrSource": "physician.name",
                },
                {
                    "fieldId": "physicianLicense",
                    "label": "License number",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "physicianName",
                    "emrSource": "physician.licenseNumber",
                },
                {
                    "fieldId": "clinicAddress",
                    "label": "Clinic address",
                    "fieldType": "textarea",
                    "required": True,
                    "piiClassification": "address",
                    "emrSource": "physician.clinicAddress",
                },
                {
                    "fieldId": "dateOfCertification",
                    "label": "Date of certification",
                    "fieldType": "date",
                    "required": True,
                    "piiClassification": None,
                    "emrSource": None,
                    "helpText": "Auto-filled with today's date",
                },
            ],
        },
    ],
}


def getRequiredPiiFields() -> List[str]:
    """Return list of PII classifications this form requires."""
    piiFields = []
    for section in dtcFormSchema["sections"]:
        for field in section["fields"]:
            if field["piiClassification"] and field["piiClassification"] not in piiFields:
                piiFields.append(field["piiClassification"])
    return piiFields


def getFormSchema() -> dict:
    """Return the complete form schema."""
    return dtcFormSchema
