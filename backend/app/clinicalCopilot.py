"""
Clinical Copilot — PII-safe AI assistant for physicians.

The flow for every query:
  1. Detect patient name in the query (fuzzy match against DB)
  2. If patient found, load their clinical record
  3. REDACT all PII from the query + patient context → tokens
  4. Build LLM messages with system prompt + redacted context
  5. Stream LLM response (already redacted — no real PII sent)
  6. RESTORE real PII tokens in the streamed response
  7. Audit log the access

PII Safety Guarantees:
  - Patient names, DOBs, health card numbers, SINs, phone numbers, addresses
    are NEVER sent to the LLM in plaintext
  - All PII is replaced with tokens like [PATIENT_NAME_1] before LLM call
  - LLM sees: "Patient [PATIENT_NAME_1], DOB [DOB_1], diagnosis: COPD..."
  - After LLM responds, tokens are restored to real values
  - Every patient access is audit-logged with the real JWT userId
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Generator, List, Optional, Tuple

from app.llmClient import llmClient
from app.encryption.piiScrubber import redactPii, restorePii, RedactionResult, buildRedactedContext, detectTaskType
from app.patientMatcher import matchPatient
from app.models import Patient
from app.database import db
from app.piiGateway import auditPiiAccess

logger = logging.getLogger(__name__)


# ─── Patient name extraction patterns ──────────────────────────────────

# Phrases that indicate a patient is being referenced
PATIENT_CONTEXT_PATTERNS = [
    r"(?:patient|pt|see|about|for|regarding|mr\.?|mrs\.?|ms\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    r"(?:show me|pull up|look up|find|search)\s+(?:for\s+)?(?:patient\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    r"^([A-Z][a-z]+\s+[A-Z][a-z]+)",  # Name at start of message
]


def extractPatientName(query: str) -> Optional[str]:
    """
    Try to extract a patient name from the doctor's natural language query.
    Returns the first plausible name found, or None.
    """
    for pattern in PATIENT_CONTEXT_PATTERNS:
        match = re.search(pattern, query)
        if match:
            name = match.group(1).strip()
            # Filter out common false positives
            lower = name.lower()
            if lower not in ("the patient", "a patient", "this patient", "my patient"):
                if len(name) >= 3:
                    return name
    return None


def findPatient(query: str, searchPatients: List[Patient] = None) -> Optional[Tuple[Patient, float, str]]:
    """
    Find the best matching patient from the query.
    Returns (patient, score, matchType) or None.
    """
    # Extract name from query
    name = extractPatientName(query)

    # If no name found via patterns, try the whole query as a name search
    if not name:
        # Check if the query looks like it could be a name (short, capitalized words)
        words = query.strip().split()
        if 1 <= len(words) <= 4 and all(w[0].isupper() or not w[0].isalpha() for w in words):
            name = query.strip()

    if not name:
        return None

    if searchPatients is None:
        searchPatients = Patient.query.all()

    matches = matchPatient(name, searchPatients, threshold=0.4)
    if not matches:
        return None

    top = matches[0]
    return top["patient"], top["score"], top["matchType"]


# ─── System prompt (PII-safe — no real patient data) ───────────────────

SYSTEM_PROMPT = """You are Paean Clinical Copilot — an AI assistant for Canadian physicians.

You help doctors with:
- Answering clinical questions about their patients
- Drafting sick notes, referral letters, and form narratives
- Completing CRA Disability Tax Credit (T2201) forms as narrative documents
- Summarizing patient histories and medication lists
- Suggesting differential diagnoses (educational, not diagnostic)
- Checking drug interactions and contraindications

CRITICAL RULES:
1. You are an ASSISTANT, not a replacement for clinical judgment. Always defer to the physician.
2. Patient information is provided as CONTEXT — use it to answer their questions.
3. If drafting a sick note or referral letter, format it professionally with proper medical terminology.
4. NEVER output placeholders like [Physician Name], [Current Date], [Clinic Name], [Start Date], etc. Use the actual values provided in the Physician Context. If a value is not provided, omit it rather than using a placeholder.
5. When dates are needed, use the Current Date provided in the context. Calculate start/end dates from the clinical notes if specified (e.g., "3 days off" = today + 3 days).
6. Keep responses concise and clinically relevant.
7. If you don't have enough information, ask the physician — but do not use bracketed placeholders.
8. Do not include any identifying information in your responses that wasn't in the context provided.
9. When generating a sick note, include the physician's name, license, clinic name, and clinic address from the Physician Context — never leave these as placeholders.
10. When listing current medications, ALWAYS use bullet points — one medication per line with name, dose, and frequency.

Canadian healthcare context:
- Provincial billing: OHIP (Ontario)
- Drug benefit programs: ODB (Ontario Drug Benefit), Trillium
- Disability forms: DTC (T2201), CPP Disability, ODSP
- Privacy law: PHIPA (Ontario Personal Health Information Protection Act)"""


def buildContext(patient: Patient) -> str:
    """
    Build a FULL clinical context string from the patient record.
    This will be REDACTED and MINIMIZED before reaching the LLM.
    """
    lines = [
        f"Patient: {patient.patientName}",
        f"DOB: {patient.dateOfBirth or 'Unknown'}",
        f"Health Card: {patient.healthCardNumber or 'N/A'}",
        f"Diagnosis: {patient.diagnosis or 'None recorded'}",
        f"Medications: {patient.medications or 'None recorded'}",
        f"Allergies: {patient.allergies or 'None known'}",
        f"Clinical Notes: {patient.notes or 'No notes available'}",
    ]

    if patient.address:
        lines.append(f"Address: {patient.address}")
    if patient.phoneNumber:
        lines.append(f"Phone: {patient.phoneNumber}")
    if patient.email:
        lines.append(f"Email: {patient.email}")

    return "\n".join(lines)


def processCopilotQuery(
    query: str,
    userId: str,
    conversationHistory: List[Dict] = None,
) -> Dict:
    """
    Non-streaming version — returns structured result with patient match info.
    Used for the search/preview before streaming.
    """
    # Find patient
    patientMatch = findPatient(query)

    result = {
        "query": query,
        "patientFound": patientMatch is not None,
        "patient": None,
        "matchScore": None,
        "matchType": None,
        "redactedContext": None,
    }

    if patientMatch:
        patient, score, matchType = patientMatch
        result["patient"] = {
            "id": patient.id,
            "name": patient.patientName,
            "dob": patient.dateOfBirth,
            "diagnosis": patient.diagnosis,
        }
        result["matchScore"] = score
        result["matchType"] = matchType

        # Audit log the patient access
        auditPiiAccess(
            userId=userId,
            action="copilot_patient_access",
            piiFields=["patientName", "dateOfBirth", "diagnosis", "medications", "notes"],
            endpoint="/api/v1/copilot/chat",
            patientId=str(patient.id),
        )

    return result


def streamCopilotResponse(
    query: str,
    userId: str,
    conversationHistory: List[Dict] = None,
    physicianInfo: Dict = None,
) -> Generator[str, None, None]:
    """
    Stream a PII-safe copilot response.

    Flow:
      1. Find patient (fuzzy match)
      2. Build clinical context
      3. REDACT all PII → tokens
      4. Build LLM messages (including physician info + dates)
      5. Stream LLM response
      6. RESTORE PII in each chunk
      7. Yield restored chunks

    Yields: JSON event strings for SSE format
    """
    if conversationHistory is None:
        conversationHistory = []
    if physicianInfo is None:
        physicianInfo = {}

    # ─── Step 1: Find patient ─────────────────────────────────
    patientMatch = findPatient(query)

    patientContext = ""
    redactionResult = None

    if patientMatch:
        patient, score, matchType = patientMatch

        # Audit log
        auditPiiAccess(
            userId=userId,
            action="copilot_patient_access",
            piiFields=["patientName", "dateOfBirth", "diagnosis", "medications", "notes"],
            endpoint="/api/v1/copilot/chat",
            patientId=str(patient.id),
        )

        # ─── Steps 2-3: Minimize context + REDACT all PII ──────
        redactedContext, redactionResult, fieldsIncluded, taskType = buildRedactedContext(patient, query)

        # Also redact the query itself
        queryRedaction = redactPii(query)
        redactedQuery = queryRedaction.redactedText

        # Merge token maps
        mergedTokens = {}
        mergedTokens.update(redactionResult.tokenMap)
        mergedTokens.update(queryRedaction.tokenMap)

        logger.info(
            f"Copilot: Patient={patient.patientName}, task={taskType}, "
            f"fields={fieldsIncluded}, tokens={len(mergedTokens)} "
            f"(T1={sum(1 for l in redactionResult.redactionLog if l['tier']==1)}, "
            f"T2={sum(1 for l in redactionResult.redactionLog if l['tier']==2)})"
        )

        # Emit patient match event
        matchEvent = {
            "type": "patient_match",
            "data": {
                "patientId": patient.id,
                "patientName": patient.patientName,
                "matchScore": score,
                "matchType": matchType,
            }
        }
        yield f"data: {json.dumps(matchEvent)}\n\n"

        # ─── Emit redaction preview event (what the LLM actually sees) ──
        previewEvent = {
            "type": "redaction_preview",
            "data": {
                "taskType": taskType,
                "fieldsIncluded": fieldsIncluded,
                "fieldsExcluded": [f for f in ["diagnosis", "medications", "allergies", "notes"] if f not in fieldsIncluded],
                "redactedContext": redactedContext,
                "tier1Count": sum(1 for l in redactionResult.redactionLog if l["tier"] == 1),
                "tier2Count": sum(1 for l in redactionResult.redactionLog if l["tier"] == 2),
                "totalTokensRedacted": len(mergedTokens),
            }
        }
        yield f"data: {json.dumps(previewEvent)}\n\n"

    else:
        # No patient found — still redact the query for safety
        queryRedaction = redactPii(query)
        redactedQuery = queryRedaction.redactedText
        mergedTokens = queryRedaction.tokenMap

        yield f"data: {json.dumps({'type': 'no_patient', 'data': {'message': 'No specific patient found — answering as general clinical question'}})}\n\n"

    # ─── Step 4: Build LLM messages ────────────────────────────
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # ─── Inject physician context + current date ─────────────
    # This is the doctor's OWN info — they want it in the output (sick notes, etc.)
    # It does NOT need redaction — the doctor is the authenticated user
    from datetime import date
    today = date.today().isoformat()
    todayLong = date.today().strftime("%B %d, %Y")

    physicianContext = f"""Current Date: {todayLong} (ISO: {today})
Physician Name: {physicianInfo.get('physicianName', 'N/A')}
Physician License: {physicianInfo.get('physicianLicense', 'N/A')}
Clinic Name: {physicianInfo.get('clinicName', 'N/A')}
Clinic Address: {physicianInfo.get('clinicAddress', 'N/A')}
Clinic Phone: {physicianInfo.get('clinicPhone', 'N/A')}"""

    messages.append({
        "role": "system",
        "content": physicianContext,
    })

    # Add conversation history (already redacted from previous turns)
    for msg in conversationHistory[-10:]:
        messages.append(msg)

    # Add patient context (redacted + minimized) if available
    if redactionResult and redactedContext:
        messages.append({
            "role": "system",
            "content": f"Patient Context (PII redacted, context minimized for {taskType if patientMatch else 'general'} task):\n{redactedContext}"
        })

    # Add the user's query (redacted)
    messages.append({"role": "user", "content": redactedQuery})

    # ─── Step 5: Emit "thinking" event ────────────────────────
    yield f"data: {json.dumps({'type': 'thinking', 'data': {}})}\n\n"

    # ─── Step 6: Stream LLM response ──────────────────────────
    fullResponse = ""
    try:
        for chunk in llmClient.completeStream(messages, maxTokens=4096, temperature=0.3):
            fullResponse += chunk

            # ─── Step 7: RESTORE PII in each chunk ──────────────
            if mergedTokens:
                # We can only restore complete tokens — accumulate and restore at end
                # For streaming, send chunks as-is (LLM shouldn't contain real PII tokens
                # since it only saw redacted text). But if it echoes tokens back, restore them.
                restoredChunk = chunk
                for token, original in mergedTokens.items():
                    if token in restoredChunk:
                        restoredChunk = restoredChunk.replace(token, original)
                chunk = restoredChunk

            yield f"data: {json.dumps({'type': 'chunk', 'data': {'content': chunk}})}\n\n"

    except Exception as e:
        logger.error(f"Copilot streaming error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"

    # Final restore pass on the full response (catches tokens split across chunks)
    if mergedTokens and fullResponse:
        for token, original in mergedTokens.items():
            fullResponse = fullResponse.replace(token, original)

    # ─── Done event ────────────────────────────────────────────
    yield f"data: {json.dumps({'type': 'done', 'data': {'fullResponse': fullResponse}})}\n\n"
