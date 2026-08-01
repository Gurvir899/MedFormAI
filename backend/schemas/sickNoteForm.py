"""
Sick Note Form Schema.

From CMA/CFIB 2026 Report:
  - 19% of physicians classify sick notes as a major burden
  - 36% as a moderate burden
  - Average 10.4 minutes to complete
  - 136 completions per year per physician
  - Only 25% of physicians compensated
  
Sick notes are the highest-VOLUME form. Simple, repetitive, perfect for automation.
"""

from typing import List


sickNoteSchema = {
    "formId": "sickNote",
    "formName": "Medical Sick Leave Certificate",
    "formNumber": "N/A",
    "issuingBody": "Employer/School (provincial jurisdiction)",
    "averageCompletionTimeMin": 10.4,
    "averageAnnualCompletions": 136,
    "percentPhysiciansCompensated": 25,
    "percentMajorBurden": 19,
    "percentModerateBurden": 36,
    "sections": [
        {
            "sectionId": "sectionA",
            "sectionName": "Patient Information",
            "fields": [
                {
                    "fieldId": "patientName",
                    "label": "Employee/Student Name",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "patientName",
                    "emrSource": "patientName",
                },
                {
                    "fieldId": "dateOfBirth",
                    "label": "Date of Birth",
                    "fieldType": "date",
                    "required": True,
                    "piiClassification": "dateOfBirth",
                    "emrSource": "dateOfBirth",
                },
            ],
        },
        {
            "sectionId": "sectionB",
            "sectionName": "Medical Assessment",
            "fields": [
                {
                    "fieldId": "assessmentDate",
                    "label": "Date of Assessment",
                    "fieldType": "date",
                    "required": True,
                    "piiClassification": None,
                    "emrSource": None,
                    "helpText": "Auto-filled with today's date",
                },
                {
                    "fieldId": "reasonForAbsence",
                    "label": "Reason for Absence (medical condition)",
                    "fieldType": "textarea",
                    "required": True,
                    "piiClassification": "diagnosis",
                    "emrSource": "clinicalNotes",
                    "helpText": "LLM generates from clinical notes — minimum necessary only",
                },
                {
                    "fieldId": "startDate",
                    "label": "Absence Start Date",
                    "fieldType": "date",
                    "required": True,
                    "piiClassification": None,
                    "emrSource": "visitDate",
                },
                {
                    "fieldId": "expectedReturnDate",
                    "label": "Expected Return Date",
                    "fieldType": "date",
                    "required": True,
                    "piiClassification": None,
                    "emrSource": "expectedReturn",
                },
                {
                    "fieldId": "fitnessForDuty",
                    "label": "Fitness for Duty Statement",
                    "fieldType": "textarea",
                    "required": False,
                    "piiClassification": "notes",
                    "emrSource": "clinicalNotes",
                    "helpText": "LLM generates: 'Patient is medically unfit for work/school from X to Y'",
                },
            ],
        },
        {
            "sectionId": "sectionC",
            "sectionName": "Physician Information",
            "fields": [
                {
                    "fieldId": "physicianName",
                    "label": "Physician Name",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "physicianName",
                    "emrSource": "physicianName",
                },
                {
                    "fieldId": "physicianLicense",
                    "label": "CPSO/License Number",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": "physicianName",
                    "emrSource": "physicianLicense",
                },
                {
                    "fieldId": "clinicName",
                    "label": "Clinic Name",
                    "fieldType": "text",
                    "required": True,
                    "piiClassification": None,
                    "emrSource": "clinicName",
                },
                {
                    "fieldId": "clinicAddress",
                    "label": "Clinic Address",
                    "fieldType": "textarea",
                    "required": True,
                    "piiClassification": "address",
                    "emrSource": "clinicAddress",
                },
                {
                    "fieldId": "dateOfIssue",
                    "label": "Date of Issue",
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


def getSickNoteRequiredPiiFields() -> List[str]:
    piiFields = []
    for section in sickNoteSchema["sections"]:
        for field in section["fields"]:
            if field["piiClassification"] and field["piiClassification"] not in piiFields:
                piiFields.append(field["piiClassification"])
    return piiFields


def getSickNoteSchema() -> dict:
    return sickNoteSchema
