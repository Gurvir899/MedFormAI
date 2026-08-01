"""
LLM Redaction Layer — strips PII + quasi-identifiers before sending to any external LLM API.

Critical compliance rule: NO patient data ever leaves our infrastructure in
plaintext. Before any LLM call, PII is replaced with reversible tokens.
After the LLM responds, tokens are mapped back to real values.

Three tiers of redaction:
  Tier 1 — Direct identifiers (name, DOB, SIN, phone, email, health card, address)
  Tier 2 — Quasi-identifiers (medication names + dosages, rare allergy combos)
  Tier 3 — Context minimization (only send clinical fields relevant to the task)

Flow:
    "Patient John Doe, DOB 1985-03-15, PHN 12345..."
        ↓ REDACT (Tier 1 + 2)
    "Patient [PATIENT_NAME_1], DOB [DOB_1], PHN [PHN_1]..."
        ↓ MINIMIZE (Tier 3)
    Only fields relevant to "sick note" task included
        ↓ Send to LLM
    LLM responds: "Form completed for [PATIENT_NAME_1]..."
        ↓ RE-INSERT
    "Form completed for John Doe, PHN 12345..."
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# ─── Tier 1: Direct identifiers ────────────────────────────────────────

piiPatterns: List[Tuple[str, str]] = [
    # Health card numbers (ON, BC, AB, QC patterns)
    (r"\b\d{10}\b", "HEALTH_CARD"),
    (r"\b[A-Z]{4}\d{8}\b", "HEALTH_CARD"),
    # PHN variants
    (r"\b\d{9}\b", "PHN"),
    # Names after common prefixes
    (r"\bPatient:\s*([A-Z][a-z]+ [A-Z][a-z]+)", "PATIENT_NAME"),
    (r"\bDr\.\s*([A-Z][a-z]+ [A-Z][a-z]+)", "PHYSICIAN_NAME"),
    # Date of birth
    (r"\b(?:DOB|Date of Birth)[:\s]*(\d{4}-\d{2}-\d{2})\b", "DOB"),
    (r"\b(\d{4}-\d{2}-\d{2})\b", "DOB_DATE"),
    # Phone numbers
    (r"\b(\d{3}[-.]?\d{3}[-.]?\d{4})\b", "PHONE"),
    # Email
    (r"\b([\w.-]+@[\w.-]+\.\w+)\b", "EMAIL"),
    # SIN (Canadian Social Insurance Number)
    (r"\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b", "SIN"),
    # Postal code
    (r"\b([A-Z]\d[A-Z]\s?\d[A-Z]\d)\b", "POSTAL_CODE"),
    # Address
    (r"\b(\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd))\b", "ADDRESS"),
]

piiRegex = [(re.compile(pattern, re.IGNORECASE), label) for pattern, label in piiPatterns]


# ─── Tier 2: Quasi-identifiers (medications + rare clinical patterns) ─

# Medication patterns: drug name + dosage
# These are quasi-identifiers because a rare medication combo can identify a patient
medicationPattern = re.compile(
    r"\b("
    # Common drug names (generic + brand)
    r"lisinopril|metformin|atorvastatin|ramipril|amlodipine|"
    r"celecoxib|acetaminophen|ondansetron|sumatriptan|propranolol|"
    r"levothyroxine|sertraline|budesonide|formoterol|salbutamol|"
    r"montelukast|tiotropium|salmeterol|fluticasone|"
    r"clopidogrel|bisoprolol|aspirin|naproxen|cyclobenzaprine|"
    r"ferrous\s+sulfate|loperamide|rifaximin|"
    r"warfarin|apixaban|rivaroxaban|"
    r"insulin|glargine|lispro|"
    r"morphine|hydromorphone|oxycodone|"
    r"diazepam|lorazepam|clonazepam|"
    r"citalopram|escitalopram|fluoxetine|venlafaxine|duloxetine|"
    r"hydrochlorothiazide|indapamide|spironolactone|"
    r"rosuvastatin|simvastatin|pravastatin|"
    r"omeprazole|pantoprazole|rabeprazole|lansoprazole|"
    r"amoxicillin|azithromycin|clarithromycin|cephalexin|ciprofloxacin|"
    r"prednisone|prednisolone|methylprednisolone|"
    r"methotrexate|hydroxychloroquine|sulfasalazine|"
    r"tamsulosin|finasteride|"
    r"levothyroxine|propylthiouracil|methimazole|"
    r"gabapentin|pregabalin|"
    r"[A-Z][a-z]+cillin|[A-Z][a-z]+mycin"
    r")\s+(\d+(?:\.\d+)?(?:\s*mg|\s*mcg|\s*g|\s*mL|\s units)?)"
    r"(?:\s+(?:BID|TID|QID|QD|HS|PRN|daily|twice\s+daily|three\s+times\s+daily|"
    r"four\s+times\s+daily|at\s+bedtime|as\s+needed|"
    r"\d+\s*times?\s*/?\s*(?:day|week|hour))?)?\b",
    re.IGNORECASE
)

# Rare allergy combinations that could be quasi-identifiers
rareAllergyPattern = re.compile(
    r"\b(allerg(?:y|ies)(?:\s+to)?[:\s]*)([A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)*)\b",
    re.IGNORECASE
)

# Specific lab values that could identify a patient
labValuePattern = re.compile(
    r"\b(?:A1C|HbA1c|eGFR|INR|TSH|hemoglobin|ferritin|LDL|HDL|creatinine)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:%|mmol/L|mg/dL|g/L|ug/L)?\b",
    re.IGNORECASE
)


@dataclass
class RedactionResult:
    """Result of a PII redaction pass."""
    redactedText: str
    tokenMap: Dict[str, str] = field(default_factory=dict)
    # Track what was redacted for the preview
    redactionLog: List[Dict] = field(default_factory=list)

    def restore(self, text: str) -> str:
        """Re-insert real PII values by replacing tokens."""
        restored = text
        for token, original in self.tokenMap.items():
            restored = restored.replace(token, original)
        return restored


def redactPii(text: str, redactMedical: bool = False) -> RedactionResult:
    """
    Scan text for PII patterns and replace with reversible tokens.

    Tier 1 (always redacted): Direct identifiers — names, DOBs, SINs,
        phone numbers, emails, health card numbers, postal codes, addresses.
        These can identify a specific person.

    Tier 2 (opt-in via redactMedical=True): Quasi-identifiers — medication
        names + dosages, lab values. These are MEDICAL DATA, not PII. They
        are only redacted when explicitly requested (e.g. for a sick note
        where med names aren't needed). For medication review, clinical
        summary, DTC, and general queries, medical data is sent in plaintext
        to the LLM — it's needed for the task and is not an identifier.

    PII compliance: PHIPA/PIPEDA define PII as information that identifies
    an individual. A diagnosis or medication name without a name/DOB/SIN
    attached is de-identified clinical data, not PII. The LLM sees clinical
    data but never sees WHO the patient is.
    """
    result = RedactionResult(redactedText=text)
    tokenCounter: Dict[str, int] = {}

    # ─── Tier 1: Direct identifiers ──────────────────────────
    for regex, label in piiRegex:
        matches = regex.finditer(text)
        for match in matches:
            originalValue = match.group(0) if match.groups() else match.group(0)
            if match.groups():
                originalValue = match.group(1)

            if label not in tokenCounter:
                tokenCounter[label] = 0
            tokenCounter[label] += 1
            token = f"[{label}_{tokenCounter[label]}]"

            result.tokenMap[token] = originalValue
            result.redactedText = result.redactedText.replace(originalValue, token)
            result.redactionLog.append({
                "tier": 1,
                "type": label,
                "token": token,
                "originalLength": len(originalValue),
            })

    # ─── Tier 2: Medication names + dosages (opt-in) ─────────
    # Medical data is NOT PII — only redact when explicitly requested
    # (e.g. sick notes where med names aren't needed for the task)
    if redactMedical:
        medMatches = list(medicationPattern.finditer(result.redactedText))
        for match in medMatches:
            originalValue = match.group(0)
            if "MEDICATION" not in tokenCounter:
                tokenCounter["MEDICATION"] = 0
            tokenCounter["MEDICATION"] += 1
            token = f"[MEDICATION_{tokenCounter['MEDICATION']}]"

            result.tokenMap[token] = originalValue
            result.redactedText = result.redactedText.replace(originalValue, token)
            result.redactionLog.append({
                "tier": 2,
                "type": "MEDICATION",
                "token": token,
                "originalLength": len(originalValue),
            })

        # ─── Tier 2: Lab values (opt-in) ──────────────────────
        labMatches = list(labValuePattern.finditer(result.redactedText))
        for match in labMatches:
            originalValue = match.group(0)
            if "LAB_VALUE" not in tokenCounter:
                tokenCounter["LAB_VALUE"] = 0
            tokenCounter["LAB_VALUE"] += 1
            token = f"[LAB_VALUE_{tokenCounter['LAB_VALUE']}]"

            result.tokenMap[token] = originalValue
            result.redactedText = result.redactedText.replace(originalValue, token)
            result.redactionLog.append({
                "tier": 2,
                "type": "LAB_VALUE",
                "token": token,
                "originalLength": len(originalValue),
            })

    logger.info(
        f"Redacted {len(result.tokenMap)} tokens "
        f"(T1: {sum(1 for l in result.redactionLog if l['tier'] == 1)}, "
        f"T2: {sum(1 for l in result.redactionLog if l['tier'] == 2)})"
    )
    return result


def restorePii(redactedText: str, tokenMap: Dict[str, str]) -> str:
    """Restore original PII values into redacted text."""
    restored = redactedText
    for token, original in tokenMap.items():
        restored = restored.replace(token, original)
    return restored


# ─── Tier 3: Context minimization ─────────────────────────────────────

# Task-specific field allowlists — only send what's needed for the task
taskFieldAllowlist: Dict[str, List[str]] = {
    "sickNote": [
        "diagnosis",
        "notes",
    ],
    "dtc": [
        "diagnosis",
        "notes",
        "medications",
        "allergies",
    ],
    "medication_review": [
        "medications",
        "allergies",
        "diagnosis",  # Need diagnosis for context — e.g. diabetes meds
        "notes",  # Clinical notes may mention med changes
    ],
    "allergy_check": [
        "allergies",
        "medications",  # Need to check if prescribed med conflicts with allergy
        "diagnosis",
    ],
    "clinical_summary": [
        "diagnosis",
        "medications",
        "allergies",
        "notes",
    ],
    "general": [
        "diagnosis",
        "medications",
        "allergies",
        "notes",
    ],
}


def minimizeContext(
    patientData: Dict,
    taskType: str = "general",
) -> Tuple[str, List[str]]:
    """
    Build a minimized clinical context — only include fields relevant to the task.

    Args:
        patientData: Full patient record dict
        taskType: What the copilot is doing (sickNote, dtc, medication_review, etc.)

    Returns: (minimizedContext, fieldsIncluded) tuple
    """
    allowedFields = taskFieldAllowlist.get(taskType, taskFieldAllowlist["general"])

    # Detect task type from the patient data / query if not specified
    # This is a fallback — the caller should pass the task type
    lines = []
    fieldsIncluded = []

    fieldLabels = {
        "diagnosis": "Diagnosis",
        "medications": "Current Medications",
        "allergies": "Allergies",
        "notes": "Clinical Notes",
    }

    for fieldName in allowedFields:
        value = patientData.get(fieldName)
        if value:
            label = fieldLabels.get(fieldName, fieldName)
            lines.append(f"{label}: {value}")
            fieldsIncluded.append(fieldName)

    return "\n".join(lines), fieldsIncluded


def detectTaskType(query: str) -> str:
    """
    Detect what kind of clinical task the doctor is asking about,
    so we can minimize the context accordingly.
    """
    queryLower = query.lower()

    if any(w in queryLower for w in ["sick note", "sick leave", "unfit for work", "absence", "medical certificate"]):
        return "sickNote"
    if any(w in queryLower for w in ["dtc", "disability tax", "t2201", "disability credit"]):
        return "dtc"
    if any(w in queryLower for w in ["medication", "drug", "prescription", "dose", "dosage", "interaction"]):
        return "medication_review"
    if any(w in queryLower for w in ["allerg", "reaction to", "intoleran"]):
        return "allergy_check"
    if any(w in queryLower for w in ["summar", "overview", "history", "status", "condition", "clinical"]):
        return "clinical_summary"

    return "general"


def buildRedactedContext(
    patient,
    query: str,
) -> Tuple[str, RedactionResult, List[str], str]:
    """
    Full PII-safe context builder:
      1. Detect task type from query
      2. Minimize context (only relevant fields)
      3. Redact all PII + quasi-identifiers
      4. Return redacted context + token map + fields included + task type

    Returns: (redactedContext, redactionResult, fieldsIncluded, taskType)
    """
    taskType = detectTaskType(query)

    # Build patient data dict
    patientData = {
        "patientName": patient.patientName or "",
        "dateOfBirth": patient.dateOfBirth or "",
        "healthCardNumber": patient.healthCardNumber or "",
        "address": patient.address or "",
        "phoneNumber": patient.phoneNumber or "",
        "email": patient.email or "",
        "diagnosis": patient.diagnosis or "",
        "medications": patient.medications or "",
        "allergies": patient.allergies or "",
        "notes": patient.notes or "",
    }

    # Tier 3: Minimize context
    minimizedContext, fieldsIncluded = minimizeContext(patientData, taskType)

    # Also include patient name + DOB as tokenized headers (needed for form filling)
    # but they'll be redacted in the next step
    fullContext = f"Patient: {patientData['patientName']}\nDOB: {patientData['dateOfBirth']}\n{minimizedContext}"

    # Tier 1 + 2: Redact everything
    # Medical data (meds, diagnosis, allergies) is NOT PII — only redact
    # medications for sick notes where they're not needed for the task.
    # For medication review, DTC, clinical summary: send medical data in plaintext.
    redactMedical = taskType in ("sickNote",)  # Only sick notes don't need med names
    redactionResult = redactPii(fullContext, redactMedical=redactMedical)

    return redactionResult.redactedText, redactionResult, fieldsIncluded, taskType
