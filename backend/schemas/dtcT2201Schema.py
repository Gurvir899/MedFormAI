"""
DTC T2201 Form Schema — Full CRA Disability Tax Credit Certificate specification.

This schema is the single source of truth for the T2201 form structure. It is
consumed by:
  - dtcCopilot.py     (LLM chunked form generation — chunk specs mirror this skeleton)
  - dtcPdfGenerator.py (PDF rendering — reads exactly these field IDs)
  - routes.py          (API endpoints serve this schema + validation results)

The JSON skeleton in `dtcT2201Schema` matches section 13 of the T2201 spec:
  - partA:          Individual's section (person with disability, supporting
                     family member, adjustments, authorization)
  - partB:          Disability details (10 impairment categories)
  - certification:   Medical practitioner certification

Field IDs are camelCase throughout (personFirstName, walkingQ4Examples, etc.),
matching the project convention and the chunk specs in dtcCopilot.py.

Standard category object shape (speaking, hearing, walking, eliminating,
feeding, dressing):
  designation, initials, q1Diagnoses, q2Medication, q3DevicesTherapy,
  q4Examples, q5MarkedRestriction, q6AllOrSubstantiallyAll, q7YearImpaired,
  q8Prolonged12Months, q9LikelyToImprove, q9ImprovementYear

Vision, mental functions, cumulative effect, and life-sustaining therapy
have their own field sets (defined below).

Validation rules V01-V15 are implemented in `validateDtcForm()`.

From CMA/CFIB 2026 Report:
  - 53% of physicians rate the DTC as a major burden
  - 32% rate it as a moderate burden
  - Average 36.6 minutes to complete
  - Completed 32.2 times per year per physician
  - Only 45.3% of physicians are compensated
"""

from typing import Any, Dict, List


# ─── Helpers ──────────────────────────────────────────────────────────


def _standardCategory(catName: str, fields: List[dict]) -> dict:
    """Build a standard Part B category object.

    Standard categories (speaking, hearing, walking, eliminating, feeding,
    dressing) share the same field shape. Each field is defined with its
    fieldId, label, type, and required flag.
    """
    return {
        "categoryName": catName,
        "fields": fields,
    }


def _standardCategoryFields() -> List[dict]:
    """Return the standard category field definitions.

    These fields are shared by speaking, hearing, walking, eliminating,
    feeding, and dressing.
    """
    return [
        {"fieldId": "designation", "label": "Designation of medical practitioner", "type": "select",
         "required": True,
         "options": ["medicalDoctor", "nursePractitioner", "occupationalTherapist",
                     "physiotherapist", "speechLanguagePathologist"]},
        {"fieldId": "initials", "label": "Initials of practitioner", "type": "text",
         "required": False},
        {"fieldId": "q1Diagnoses", "label": "Medical conditions or diagnoses causing impairment", "type": "textarea",
         "required": True},
        {"fieldId": "q2Medication", "label": "Medication for impairment", "type": "textarea",
         "required": False},
        {"fieldId": "q3DevicesTherapy", "label": "Devices or therapy used", "type": "textarea",
         "required": False},
        {"fieldId": "q4Examples", "label": "Examples of how impairment restricts the activity", "type": "textarea",
         "required": True, "helpText": "2-3 sentences of clinical detail"},
        {"fieldId": "q5MarkedRestriction", "label": "Marked restriction (unable or takes 3x longer)", "type": "boolean",
         "required": True},
        {"fieldId": "q6AllOrSubstantiallyAll", "label": "All or substantially all the time (90%+)", "type": "boolean",
         "required": True},
        {"fieldId": "q7YearImpaired", "label": "Year impairment began", "type": "text",
         "required": True},
        {"fieldId": "q8Prolonged12Months", "label": "Prolonged (lasted or expected to last 12+ continuous months)", "type": "boolean",
         "required": True},
        {"fieldId": "q9LikelyToImprove", "label": "Likely to improve", "type": "triState",
         "required": True, "options": ["yes", "no", "unsure"]},
        {"fieldId": "q9ImprovementYear", "label": "Expected year of improvement", "type": "text",
         "required": False},
    ]


# ─── DTC T2201 Schema Definition ──────────────────────────────────────


dtcT2201Schema: Dict[str, Any] = {
    "formId": "dtcT2201",
    "formName": "Disability Tax Credit Certificate (T2201)",
    "formNumber": "T2201",
    "formEdition": "T2201 E (23)",
    "issuingBody": "Canada Revenue Agency (CRA)",
    "protectedStatus": "Protected B when completed",
    "contactInfo": "canada.ca/disability-tax-credit · 1-800-959-8281",
    "averageCompletionTimeMin": 36.6,
    "averageAnnualCompletions": 32.2,
    "percentPhysiciansCompensated": 45.3,
    "percentMajorBurden": 53,
    "percentModerateBurden": 32,

    # ─── Top-level structure ───────────────────────────────────────
    "sections": ["partA", "partB", "certification"],

    "partA": {
        "sectionName": "Part A — Individual's Section",
        "subsections": ["personWithDisability", "supportingFamilyMember", "adjustments", "authorization"],
        "personWithDisability": {
            "subsectionName": "Person with the Disability",
            "fields": [
                {"fieldId": "personFirstName", "label": "First name", "type": "text", "required": True, "piiClassification": "patientName"},
                {"fieldId": "personLastName", "label": "Last name", "type": "text", "required": True, "piiClassification": "patientName"},
                {"fieldId": "personSin", "label": "Social Insurance Number", "type": "text", "required": True, "piiClassification": "sin"},
                {"fieldId": "personDateOfBirth", "label": "Date of birth", "type": "date", "required": True, "piiClassification": "dateOfBirth"},
                {"fieldId": "personMailingAddress", "label": "Mailing address", "type": "textarea", "required": True, "piiClassification": "address"},
                {"fieldId": "personCity", "label": "City", "type": "text", "required": True, "piiClassification": "address"},
                {"fieldId": "personProvince", "label": "Province", "type": "text", "required": True, "piiClassification": "address"},
                {"fieldId": "personPostalCode", "label": "Postal code", "type": "text", "required": True, "piiClassification": "address"},
            ],
        },
        "supportingFamilyMember": {
            "subsectionName": "Supporting Family Member Claiming the Amount",
            "fields": [
                {"fieldId": "claimantFirstName", "label": "First name", "type": "text", "required": False, "piiClassification": "patientName"},
                {"fieldId": "claimantLastName", "label": "Last name", "type": "text", "required": False, "piiClassification": "patientName"},
                {"fieldId": "claimantRelationship", "label": "Relationship to person with disability", "type": "text", "required": False},
                {"fieldId": "claimantSin", "label": "Social Insurance Number", "type": "text", "required": False, "piiClassification": "sin"},
                {"fieldId": "claimantCohabitates", "label": "Cohabitates with person with disability", "type": "boolean", "required": False},
                {"fieldId": "claimantProvidesFood", "label": "Provides food", "type": "boolean", "required": False},
                {"fieldId": "claimantProvidesShelter", "label": "Provides shelter", "type": "boolean", "required": False},
                {"fieldId": "claimantProvidesClothing", "label": "Provides clothing", "type": "boolean", "required": False},
                {"fieldId": "claimantSupportDetails", "label": "Support details", "type": "textarea", "required": False},
                {"fieldId": "claimantSignature", "label": "Signature", "type": "text", "required": False},
            ],
        },
        "adjustments": {
            "subsectionName": "Previous Tax Return Adjustments",
            "fields": [
                {"fieldId": "isSelfOrLegalRep", "label": "Filing as self or legal representative", "type": "boolean", "required": True},
                {"fieldId": "adjustPreviousReturns", "label": "Adjust previous tax returns", "type": "boolean", "required": False},
            ],
        },
        "authorization": {
            "subsectionName": "Individual's Authorization",
            "fields": [
                {"fieldId": "partAQ4Signature", "label": "Signature", "type": "text", "required": True},
                {"fieldId": "partAQ4Telephone", "label": "Telephone number", "type": "text", "required": True, "piiClassification": "phoneNumber"},
                {"fieldId": "partAQ4Date", "label": "Date", "type": "date", "required": True},
            ],
        },
    },

    "partB": {
        "sectionName": "Part B — Disability Details",
        "patientNameHeader": {
            "fieldId": "patientNameHeader", "label": "Patient name (header)", "type": "text", "required": False,
            "helpText": "Auto-derived from personFirstName + personLastName",
        },
        "categories": ["speaking", "hearing", "walking", "eliminating", "feeding", "dressing", "vision", "mentalFunctions", "cumulativeEffect", "lifeSustainingTherapy"],

        # ─── Standard categories (shared field shape) ─────────────
        "speaking": _standardCategory("Speaking", _standardCategoryFields()),
        "hearing": _standardCategory("Hearing", _standardCategoryFields()),
        "walking": _standardCategory("Walking", _standardCategoryFields()),
        "eliminating": _standardCategory("Eliminating (Bladder and Bowel Functions)", _standardCategoryFields()),
        "feeding": _standardCategory("Feeding", _standardCategoryFields()),
        "dressing": _standardCategory("Dressing", _standardCategoryFields()),

        # ─── Vision (special category) ───────────────────────────
        "vision": {
            "categoryName": "Vision",
            "fields": [
                {"fieldId": "visionDesignation", "label": "Designation of medical practitioner", "type": "select", "required": True,
                 "options": ["medicalDoctor", "nursePractitioner", "optometrist", "occupationalTherapist"]},
                {"fieldId": "visionQ1Diagnoses", "label": "Medical conditions or diagnoses causing visual impairment", "type": "textarea", "required": True},
                {"fieldId": "visionQ2AspectImpaired", "label": "Aspect of vision impaired", "type": "select", "required": True,
                 "options": ["visualAcuity", "fieldOfVision", "both"]},
                {"fieldId": "visionLeftAcuityType", "label": "Left eye — acuity type", "type": "text", "required": False,
                 "helpText": "e.g., 20/200, counting fingers, light perception, no light perception"},
                {"fieldId": "visionLeftAcuitySnellen", "label": "Left eye — Snellen acuity", "type": "text", "required": False},
                {"fieldId": "visionLeftFieldDegrees", "label": "Left eye — visual field (degrees)", "type": "number", "required": False},
                {"fieldId": "visionRightAcuityType", "label": "Right eye — acuity type", "type": "text", "required": False,
                 "helpText": "e.g., 20/200, counting fingers, light perception, no light perception"},
                {"fieldId": "visionRightAcuitySnellen", "label": "Right eye — Snellen acuity", "type": "text", "required": False},
                {"fieldId": "visionRightFieldDegrees", "label": "Right eye — visual field (degrees)", "type": "number", "required": False},
                {"fieldId": "visionQ3MeetsCriteria", "label": "Meets criteria in both eyes (acuity 20/200 or field ≤20 degrees)", "type": "boolean", "required": True},
                {"fieldId": "visionQ4YearImpaired", "label": "Year impairment began", "type": "text", "required": True},
                {"fieldId": "visionQ5Prolonged12Months", "label": "Prolonged (12+ continuous months)", "type": "boolean", "required": True},
                {"fieldId": "visionQ6LikelyToImprove", "label": "Likely to improve", "type": "triState", "required": True, "options": ["yes", "no", "unsure"]},
                {"fieldId": "visionQ6ImprovementYear", "label": "Expected year of improvement", "type": "text", "required": False},
            ],
        },

        # ─── Mental Functions (special category) ────────────────
        "mentalFunctions": {
            "categoryName": "Mental Functions Necessary for Everyday Life",
            "fields": [
                {"fieldId": "mentalDesignation", "label": "Designation of medical practitioner", "type": "select", "required": True,
                 "options": ["medicalDoctor", "nursePractitioner", "occupationalTherapist", "psychologist"]},
                {"fieldId": "mentalQ1Diagnoses", "label": "Medical conditions or diagnoses", "type": "textarea", "required": True},
                {"fieldId": "mentalQ2Medication", "label": "Medication", "type": "textarea", "required": False},
                {"fieldId": "mentalQ2SupervisionForMedication", "label": "Requires supervision for medication", "type": "boolean", "required": False},
                {"fieldId": "mentalQ2MedicationEffectiveness", "label": "Medication effectiveness", "type": "textarea", "required": False},
                {"fieldId": "mentalQ3DevicesTherapy", "label": "Devices or therapy used", "type": "textarea", "required": False},
                {"fieldId": "mentalQ4ImpairedIndependence", "label": "Impaired independence in everyday life", "type": "boolean", "required": True},
                {"fieldId": "mentalQ4SupportTypesAdult", "label": "Support types (adult)", "type": "text", "required": False,
                 "helpText": "e.g., daily supervision, assistance with tasks"},
                {"fieldId": "mentalQ4SupportTypesChild", "label": "Support types (child)", "type": "text", "required": False,
                 "helpText": "e.g., beyond what children of similar age need"},
                {"fieldId": "mentalQ4SupportDetails", "label": "Support details", "type": "textarea", "required": False},
                {"fieldId": "mentalQ6Examples", "label": "Examples of how mental functions are restricted", "type": "textarea", "required": True,
                 "helpText": "2-3 sentences of clinical detail"},
                {"fieldId": "mentalQ7MarkedRestriction", "label": "Marked restriction", "type": "boolean", "required": True},
                {"fieldId": "mentalQ8AllOrSubstantiallyAll", "label": "All or substantially all the time (90%+)", "type": "boolean", "required": True},
                {"fieldId": "mentalQ9YearImpaired", "label": "Year impairment began", "type": "text", "required": True},
                {"fieldId": "mentalQ10Prolonged12Months", "label": "Prolonged (12+ continuous months)", "type": "boolean", "required": True},
                {"fieldId": "mentalQ11LikelyToImprove", "label": "Likely to improve", "type": "triState", "required": True, "options": ["yes", "no", "unsure"]},
                {"fieldId": "mentalQ11ImprovementYear", "label": "Expected year of improvement", "type": "text", "required": False},
            ],
            "limitationAssessmentGrid": [
                {"fieldId": "mentalGridAdaptChange", "label": "Adapt to change", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridExpressBasicNeeds", "label": "Express basic needs", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridGoIntoCommunity", "label": "Go into the community", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridInitiateTransactions", "label": "Initiate and respond to transactions", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridBasicHygiene", "label": "Basic hygiene", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridEverydayTasks", "label": "Carry out everyday tasks", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridAwarenessOfDanger", "label": "Awareness of danger", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridImpulseControl", "label": "Impulse control", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridFocusSimpleTask", "label": "Focus on a simple task", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridShortTermInformation", "label": "Retain short-term information", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridCarryOutPlans", "label": "Carry out plans", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridSelfDirectTasks", "label": "Self-direct tasks", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridWeatherClothing", "label": "Select weather-appropriate clothing", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridTreatmentDecisions", "label": "Make treatment decisions", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridRecognizeExploitation", "label": "Recognize exploitation", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridUnderstandConsequences", "label": "Understand consequences of behaviour", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridRememberPersonalInfo", "label": "Remember personal information", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridRememberMaterialOfInterest", "label": "Remember material of interest", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridRememberInstructions", "label": "Remember instructions", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridUnderstandingOfReality", "label": "Understanding of reality", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridDistinguishDelusions", "label": "Distinguish delusions from reality", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridIdentifyProblems", "label": "Identify problems", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridImplementSolutions", "label": "Implement solutions", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridBehaveAppropriately", "label": "Behave appropriately", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridEmotionalResponses", "label": "Emotional responses", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridRegulateMood", "label": "Regulate mood", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridNonVerbalCues", "label": "Understand non-verbal cues", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
                {"fieldId": "mentalGridVerbalInformation", "label": "Process verbal information", "type": "select", "options": ["noLimitations", "someLimitations", "severeLimitations"]},
            ],
        },

        # ─── Cumulative Effect (special category) ────────────────
        "cumulativeEffect": {
            "categoryName": "Cumulative Effect of Significant Limitations",
            "fields": [
                {"fieldId": "cumulativeDesignation", "label": "Designation of medical practitioner", "type": "select", "required": True,
                 "options": ["medicalDoctor", "nursePractitioner", "occupationalTherapist", "physiotherapist", "speechLanguagePathologist", "psychologist"]},
                {"fieldId": "cumulativeQ1Categories", "label": "Categories with significant limitations", "type": "array", "required": True,
                 "options": ["vision", "speaking", "hearing", "walking", "eliminating", "feeding", "dressing", "mentalFunctions"],
                 "helpText": "Select 2 or more categories"},
                {"fieldId": "cumulativeQ2Examples", "label": "Examples of cumulative limitations", "type": "textarea", "required": True,
                 "helpText": "2-3 sentences of clinical detail"},
                {"fieldId": "cumulativeQ3ExistTogether", "label": "Limitations exist together", "type": "boolean", "required": True},
                {"fieldId": "cumulativeQ4EquivalentToMarked", "label": "Cumulative effect equivalent to a marked restriction", "type": "boolean", "required": True},
                {"fieldId": "cumulativeQ5YearBegan", "label": "Year cumulative effect began", "type": "text", "required": True},
                {"fieldId": "cumulativeQ6Prolonged12Months", "label": "Prolonged (12+ continuous months)", "type": "boolean", "required": True},
                {"fieldId": "cumulativeQ7LikelyToImprove", "label": "Likely to improve", "type": "triState", "required": True, "options": ["yes", "no", "unsure"]},
                {"fieldId": "cumulativeQ7ImprovementYear", "label": "Expected year of improvement", "type": "text", "required": False},
            ],
        },

        # ─── Life-Sustaining Therapy (special category) ─────────
        "lifeSustainingTherapy": {
            "categoryName": "Life-Sustaining Therapy",
            "fields": [
                {"fieldId": "lstDesignation", "label": "Designation of medical practitioner", "type": "select", "required": True,
                 "options": ["medicalDoctor", "nursePractitioner", "occupationalTherapist", "physiotherapist"]},
                {"fieldId": "lstQ1DiabetesDiagnosisTiming", "label": "Type 1 diabetes diagnosis timing (if applicable)", "type": "text", "required": False,
                 "helpText": "e.g., before age 14, after age 14"},
                {"fieldId": "lstQ1DiabetesDiagnosisYear", "label": "Type 1 diabetes diagnosis year", "type": "text", "required": False},
                {"fieldId": "lstQ2TherapyTypes", "label": "Therapy types", "type": "array", "required": True,
                 "options": ["insulin", "dialysis", "chestPhysiotherapy", "oxygenTherapy", "parenteralNutrition", "other"],
                 "helpText": "Select all that apply"},
                {"fieldId": "lstQ2TherapyOther", "label": "Other therapy (specify)", "type": "text", "required": False},
                {"fieldId": "lstQ2MedicalConditions", "label": "Medical conditions requiring therapy", "type": "array", "required": True,
                 "options": ["type1Diabetes", "endStageRenalDisease", "cysticFibrosis", "other"],
                 "helpText": "Select all that apply"},
                {"fieldId": "lstQ2ConditionOther", "label": "Other condition (specify)", "type": "text", "required": False},
                {"fieldId": "lstQ3EligibleActivities", "label": "Eligible therapy activities", "type": "array", "required": True,
                 "options": ["medicationAdministration", "treatmentSessions", "travelForTherapy", "setupPreparation", "other"],
                 "helpText": "Activities that count toward the 14-hour threshold"},
                {"fieldId": "lstQ4SupportsVitalFunction", "label": "Therapy supports a vital function", "type": "boolean", "required": True},
                {"fieldId": "lstQ5TimesPerWeek", "label": "Times per week", "type": "number", "required": True,
                 "helpText": "Must be ≥ 2 times per week"},
                {"fieldId": "lstQ6HoursPerWeek", "label": "Hours per week", "type": "number", "required": True,
                 "helpText": "Must be ≥ 14 hours per week"},
                {"fieldId": "lstQ7YearBegan", "label": "Year therapy began", "type": "text", "required": True},
                {"fieldId": "lstQ8Prolonged12Months", "label": "Prolonged (12+ continuous months)", "type": "boolean", "required": True},
                {"fieldId": "lstQ9LikelyToImprove", "label": "Likely to improve", "type": "triState", "required": True, "options": ["yes", "no", "unsure"]},
                {"fieldId": "lstQ9ImprovementYear", "label": "Expected year of improvement", "type": "text", "required": False},
            ],
        },
    },

    "certification": {
        "sectionName": "Certification",
        "fields": [
            {"fieldId": "certYearFrom", "label": "Certification year (from)", "type": "text", "required": True},
            {"fieldId": "certYearTo", "label": "Certification year (to)", "type": "text", "required": True},
            {"fieldId": "certHasMedicalInfoOnFile", "label": "Medical information on file", "type": "boolean", "required": True},
            {"fieldId": "certPractitionerType", "label": "Type of medical practitioner", "type": "select", "required": True,
             "options": ["medicalDoctor", "nursePractitioner", "optometrist", "occupationalTherapist", "audiologist", "physiotherapist", "psychologist", "speechLanguagePathologist"]},
            {"fieldId": "certSignature", "label": "Signature", "type": "text", "required": True,
             "helpText": "\"unsigned\" until physician signs"},
            {"fieldId": "certNamePrinted", "label": "Name (printed)", "type": "text", "required": True, "piiClassification": "physicianName"},
            {"fieldId": "certLicenseNumber", "label": "License number", "type": "text", "required": True, "piiClassification": "physicianName"},
            {"fieldId": "certTelephone", "label": "Telephone number", "type": "text", "required": True, "piiClassification": "phoneNumber"},
            {"fieldId": "certDate", "label": "Date", "type": "date", "required": True},
            {"fieldId": "certAddress", "label": "Address", "type": "textarea", "required": True, "piiClassification": "address"},
        ],
    },
}


# ─── Standard category IDs ────────────────────────────────────────────


STANDARD_CATEGORIES = ["speaking", "hearing", "walking", "eliminating", "feeding", "dressing"]
SPECIAL_CATEGORIES = ["vision", "mentalFunctions", "cumulativeEffect", "lifeSustainingTherapy"]
ALL_CATEGORIES = STANDARD_CATEGORIES + SPECIAL_CATEGORIES


# ─── Public API ────────────────────────────────────────────────────────


def getDtcT2201Schema() -> dict:
    """Return the complete DTC T2201 form schema."""
    return dtcT2201Schema


def getDtcT2201FieldList() -> List[dict]:
    """Return a flat list of all field definitions in the schema.

    Each item: {"fieldId": str, "label": str, "type": str, "required": bool,
                "section": str, "category": str | None}
    """
    flat: List[dict] = []
    schema = dtcT2201Schema

    # ─── Part A ─────────────────────────────────────────────────
    partA = schema["partA"]
    for subKey in partA.get("subsections", []):
        sub = partA.get(subKey, {})
        for field in sub.get("fields", []):
            flat.append({
                "fieldId": field["fieldId"],
                "label": field["label"],
                "type": field["type"],
                "required": field.get("required", False),
                "section": "partA",
                "category": subKey,
            })

    # ─── Part B ─────────────────────────────────────────────────
    partB = schema["partB"]

    # patientNameHeader
    header = partB.get("patientNameHeader", {})
    flat.append({
        "fieldId": header["fieldId"],
        "label": header["label"],
        "type": header["type"],
        "required": header.get("required", False),
        "section": "partB",
        "category": None,
    })

    # All categories
    for catKey in ALL_CATEGORIES:
        cat = partB.get(catKey, {})
        for field in cat.get("fields", []):
            flat.append({
                "fieldId": field["fieldId"],
                "label": field["label"],
                "type": field["type"],
                "required": field.get("required", False),
                "section": "partB",
                "category": catKey,
            })
        # Mental functions limitation assessment grid
        for gridField in cat.get("limitationAssessmentGrid", []):
            flat.append({
                "fieldId": gridField["fieldId"],
                "label": gridField["label"],
                "type": gridField["type"],
                "required": gridField.get("required", False),
                "section": "partB",
                "category": catKey,
                "grid": True,
            })

    # ─── Certification ──────────────────────────────────────────
    cert = schema["certification"]
    for field in cert.get("fields", []):
        flat.append({
            "fieldId": field["fieldId"],
            "label": field["label"],
            "type": field["type"],
            "required": field.get("required", False),
            "section": "certification",
            "category": None,
        })

    return flat


# ─── Validation (V01-V15) ─────────────────────────────────────────────


def _isFilled(value) -> bool:
    """Check if a field value is 'filled' (not null, not empty string, not empty list)."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, (list, dict)) and len(value) == 0:
        return False
    return True


def _getCategory(formData: dict, catKey: str) -> dict:
    """Safely retrieve a Part B category object from form data."""
    return (formData.get("partB") or {}).get(catKey) or {}


def _categoryIsFilled(catData: dict) -> bool:
    """Check if a category has any field filled (designation or any q-field)."""
    if not catData or not isinstance(catData, dict):
        return False
    return any(_isFilled(v) for v in catData.values())


def _validateStandardCategory(catKey: str, catData: dict) -> List[dict]:
    """Validate a standard Part B category (speaking, hearing, walking, etc.).

    Returns a list of error dicts.
    """
    errors = []

    # V06: If a standard category is filled, it must have designation
    if _categoryIsFilled(catData) and not _isFilled(catData.get("designation")):
        errors.append({
            "rule": "V06",
            "field": f"{catKey}.designation",
            "message": f"{catKey}: designation is required when the category is filled",
        })

    # V07: If a standard category is filled, q4Examples must not be empty
    if _categoryIsFilled(catData) and not _isFilled(catData.get("q4Examples")):
        errors.append({
            "rule": "V07",
            "field": f"{catKey}.q4Examples",
            "message": f"{catKey}: examples of impairment (q4Examples) is required when the category is filled",
        })

    return errors


def validateDtcForm(formData: dict) -> dict:
    """Validate a filled T2201 form against rules V01-V15.

    Rules:
      V01  partA.personWithDisability must have personFirstName + personLastName
      V02  partA.authorization must have partAQ4Signature, partAQ4Telephone, partAQ4Date
      V03  certification must have certNamePrinted, certLicenseNumber, certDate, certAddress
      V04  certification.certPractitionerType must be a valid value
      V05  At least one Part B category must be filled (eligibility requirement)
      V06  Any filled standard category must have designation
      V07  Any filled standard category must have q4Examples
      V08  Any filled category must have its prolonged-12-months field set to True
      V09  If a category has q5MarkedRestriction=True, q6AllOrSubstantiallyAll should be set (warning)
      V10  cumulativeEffect requires cumulativeQ1Categories with 2+ items
      V11  lifeSustainingTherapy requires lstQ5TimesPerWeek ≥ 2 and lstQ6HoursPerWeek ≥ 14
      V12  partA.personWithDisability must have personSin (9-digit SIN)
      V13  certification.certYearFrom must be ≤ certYearTo (if both present)
      V14  mentalFunctions: if filled, mentalQ6Examples must not be empty
      V15  vision: if filled, visionQ3MeetsCriteria must be set

    Returns:
        {"passed": bool, "errors": [...], "warnings": [...]}
    """
    errors: List[dict] = []
    warnings: List[dict] = []

    if not formData or not isinstance(formData, dict):
        return {
            "passed": False,
            "errors": [{"rule": "V00", "field": None, "message": "Form data is empty or invalid"}],
            "warnings": [],
        }

    partA = formData.get("partA") or {}
    partB = formData.get("partB") or {}
    cert = formData.get("certification") or {}

    # ─── V01: Person with disability name ───────────────────────
    pwd = partA.get("personWithDisability") or {}
    if not _isFilled(pwd.get("personFirstName")):
        errors.append({
            "rule": "V01", "field": "partA.personWithDisability.personFirstName",
            "message": "Person with disability: first name is required",
        })
    if not _isFilled(pwd.get("personLastName")):
        errors.append({
            "rule": "V01", "field": "partA.personWithDisability.personLastName",
            "message": "Person with disability: last name is required",
        })

    # ─── V02: Part A authorization ──────────────────────────────
    auth = partA.get("authorization") or {}
    for fieldId in ["partAQ4Signature", "partAQ4Telephone", "partAQ4Date"]:
        if not _isFilled(auth.get(fieldId)):
            errors.append({
                "rule": "V02", "field": f"partA.authorization.{fieldId}",
                "message": f"Part A authorization: {fieldId} is required",
            })

    # ─── V03: Certification required fields ─────────────────────
    for fieldId in ["certNamePrinted", "certLicenseNumber", "certDate", "certAddress"]:
        if not _isFilled(cert.get(fieldId)):
            errors.append({
                "rule": "V03", "field": f"certification.{fieldId}",
                "message": f"Certification: {fieldId} is required",
            })

    # ─── V04: certPractitionerType valid ───────────────────────
    validPractitionerTypes = {
        "medicalDoctor", "nursePractitioner", "optometrist", "occupationalTherapist",
        "audiologist", "physiotherapist", "psychologist", "speechLanguagePathologist",
    }
    certType = cert.get("certPractitionerType")
    if _isFilled(certType) and certType not in validPractitionerTypes:
        errors.append({
            "rule": "V04", "field": "certification.certPractitionerType",
            "message": f"Certification: practitioner type '{certType}' is not valid",
        })

    # ─── V05: At least one Part B category filled ───────────────
    filledCategories = []
    for catKey in ALL_CATEGORIES:
        catData = _getCategory(formData, catKey)
        if _categoryIsFilled(catData):
            filledCategories.append(catKey)

    if not filledCategories:
        errors.append({
            "rule": "V05", "field": "partB",
            "message": "At least one Part B impairment category must be completed",
        })

    # ─── V06 + V07: Standard category designation + q4Examples ─
    for catKey in STANDARD_CATEGORIES:
        catData = _getCategory(formData, catKey)
        if _categoryIsFilled(catData):
            if not _isFilled(catData.get("designation")):
                errors.append({
                    "rule": "V06", "field": f"partB.{catKey}.designation",
                    "message": f"{catKey}: designation is required when the category is filled",
                })
            if not _isFilled(catData.get("q4Examples")):
                errors.append({
                    "rule": "V07", "field": f"partB.{catKey}.q4Examples",
                    "message": f"{catKey}: examples of impairment (q4Examples) is required when the category is filled",
                })

    # ─── V08: Prolonged 12+ months ─────────────────────────────
    prolongedFields = {
        "speaking": "q8Prolonged12Months",
        "hearing": "q8Prolonged12Months",
        "walking": "q8Prolonged12Months",
        "eliminating": "q8Prolonged12Months",
        "feeding": "q8Prolonged12Months",
        "dressing": "q8Prolonged12Months",
        "vision": "visionQ5Prolonged12Months",
        "mentalFunctions": "mentalQ10Prolonged12Months",
        "cumulativeEffect": "cumulativeQ6Prolonged12Months",
        "lifeSustainingTherapy": "lstQ8Prolonged12Months",
    }
    for catKey, prolongedField in prolongedFields.items():
        catData = _getCategory(formData, catKey)
        if _categoryIsFilled(catData):
            val = catData.get(prolongedField)
            if val is not True:
                errors.append({
                    "rule": "V08", "field": f"partB.{catKey}.{prolongedField}",
                    "message": f"{catKey}: {prolongedField} must be true (impairment must last 12+ continuous months)",
                })

    # ─── V09: q5MarkedRestriction → q6AllOrSubstantiallyAll (warn) ─
    for catKey in STANDARD_CATEGORIES:
        catData = _getCategory(formData, catKey)
        if _categoryIsFilled(catData) and catData.get("q5MarkedRestriction") is True:
            if catData.get("q6AllOrSubstantiallyAll") is None:
                warnings.append({
                    "rule": "V09", "field": f"partB.{catKey}.q6AllOrSubstantiallyAll",
                    "message": f"{catKey}: q5MarkedRestriction is true but q6AllOrSubstantiallyAll is not set",
                })

    # ─── V10: Cumulative effect requires 2+ categories ──────────
    cum = _getCategory(formData, "cumulativeEffect")
    if _categoryIsFilled(cum):
        cats = cum.get("cumulativeQ1Categories")
        if not _isFilled(cats) or not isinstance(cats, list) or len(cats) < 2:
            errors.append({
                "rule": "V10", "field": "partB.cumulativeEffect.cumulativeQ1Categories",
                "message": "Cumulative effect: cumulativeQ1Categories must list 2 or more categories",
            })

    # ─── V11: Life-sustaining therapy thresholds ───────────────
    lst = _getCategory(formData, "lifeSustainingTherapy")
    if _categoryIsFilled(lst):
        timesPerWeek = lst.get("lstQ5TimesPerWeek")
        if timesPerWeek is not None:
            try:
                if float(timesPerWeek) < 2:
                    errors.append({
                        "rule": "V11", "field": "partB.lifeSustainingTherapy.lstQ5TimesPerWeek",
                        "message": "Life-sustaining therapy: lstQ5TimesPerWeek must be ≥ 2",
                    })
            except (ValueError, TypeError):
                errors.append({
                    "rule": "V11", "field": "partB.lifeSustainingTherapy.lstQ5TimesPerWeek",
                    "message": "Life-sustaining therapy: lstQ5TimesPerWeek must be a number ≥ 2",
                })

        hoursPerWeek = lst.get("lstQ6HoursPerWeek")
        if hoursPerWeek is not None:
            try:
                if float(hoursPerWeek) < 14:
                    errors.append({
                        "rule": "V11", "field": "partB.lifeSustainingTherapy.lstQ6HoursPerWeek",
                        "message": "Life-sustaining therapy: lstQ6HoursPerWeek must be ≥ 14",
                    })
            except (ValueError, TypeError):
                errors.append({
                    "rule": "V11", "field": "partB.lifeSustainingTherapy.lstQ6HoursPerWeek",
                    "message": "Life-sustaining therapy: lstQ6HoursPerWeek must be a number ≥ 14",
                })

    # ─── V12: SIN format (9 digits) ─────────────────────────────
    sin = pwd.get("personSin")
    if _isFilled(sin):
        sinDigits = re.sub(r"\D", "", str(sin))
        if len(sinDigits) != 9:
            errors.append({
                "rule": "V12", "field": "partA.personWithDisability.personSin",
                "message": f"Person with disability: SIN must be 9 digits (got {len(sinDigits)})",
            })

    # ─── V13: certYearFrom ≤ certYearTo ─────────────────────────
    yearFrom = cert.get("certYearFrom")
    yearTo = cert.get("certYearTo")
    if _isFilled(yearFrom) and _isFilled(yearTo):
        try:
            if int(yearFrom) > int(yearTo):
                errors.append({
                    "rule": "V13", "field": "certification.certYearFrom",
                    "message": f"Certification: certYearFrom ({yearFrom}) cannot be after certYearTo ({yearTo})",
                })
        except (ValueError, TypeError):
            pass

    # ─── V14: Mental functions mentalQ6Examples ────────────────
    mental = _getCategory(formData, "mentalFunctions")
    if _categoryIsFilled(mental) and not _isFilled(mental.get("mentalQ6Examples")):
        errors.append({
            "rule": "V14", "field": "partB.mentalFunctions.mentalQ6Examples",
            "message": "Mental functions: mentalQ6Examples is required when the category is filled",
        })

    # ─── V15: Vision visionQ3MeetsCriteria ─────────────────────
    vision = _getCategory(formData, "vision")
    if _categoryIsFilled(vision) and vision.get("visionQ3MeetsCriteria") is None:
        errors.append({
            "rule": "V15", "field": "partB.vision.visionQ3MeetsCriteria",
            "message": "Vision: visionQ3MeetsCriteria must be set when the category is filled",
        })

    passed = len(errors) == 0
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
    }


# ─── Late import for V12 (SIN regex) ──────────────────────────────────

import re
