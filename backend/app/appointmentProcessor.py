"""
Appointment Processor — takes a doctor's clinical note, uses LLM to extract
structured patient field updates, and applies them to the patient record.

Flow:
  1. Doctor writes free-text clinical note during/after appointment
  2. PII redaction layer strips identifiers → tokens
  3. LLM (spur-gemma4) extracts structured updates: diagnosis, medications,
     allergies, notes, disability checkmarks, yearImpaired, devicesTherapy
  4. Tokens restored in the response
  5. Doctor reviews the extracted updates before they're applied
  6. On confirm, updates are written to the Patient record
  7. Appointment record saved with clinical note + AI summary + field updates

PII Safety: Same 3-tier redaction as copilot — LLM never sees real identifiers.
"""

import json
import logging
from typing import Dict, Tuple

from app.llmClient import llmClient
from app.encryption.piiScrubber import redactPii, restorePii, buildRedactedContext

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a clinical assistant for a Canadian physician. The doctor has written a clinical note after seeing a patient. Your job is to extract structured patient field updates from the note.

Extract these fields if mentioned in the note:
- diagnosis: The patient's current diagnosis(es)
- medications: Current medications (name + dose + frequency)
- allergies: Known allergies
- notes: Clinical assessment + plan (the doctor's own summary)
- disabilityWalking: True if the note mentions difficulty walking, mobility issues, or needing a cane/walker
- disabilityDressing: True if difficulty dressing, bathing, or upper body mobility issues
- disabilityFeeding: True if difficulty feeding themselves or needs tube feeding
- disabilitySpeaking: True if speech impairment
- disabilityHearing: True if hearing impairment
- disabilityVision: True if vision impairment
- disabilityEliminating: True if bowel/bladder management issues, incontinence, catheter
- disabilityMental: True if mental function impairment, cognitive issues, psychiatric condition
- disabilityIndependentLiving: True if patient cannot live independently, needs daily help
- disabilityTherapy: True if receiving life-sustaining therapy (dialysis, oxygen, insulin, tube feeding)
- yearImpaired: The year the condition started or was diagnosed (integer, e.g. 2019)
- devicesTherapy: Any walking aids, hearing aids, medical devices, or therapy the patient uses

Rules:
1. Only include fields the note actually mentions. Omit fields not mentioned (set to null).
2. For boolean fields, use true/false. If not mentioned, use null.
3. For text fields, write the value as stated in the note.
4. Do NOT invent information — only extract what the doctor wrote.
5. Respond with JSON only. No markdown, no explanation.

Format:
{
  "diagnosis": null,
  "medications": null,
  "allergies": null,
  "notes": null,
  "disabilityWalking": null,
  "disabilityDressing": null,
  "disabilityFeeding": null,
  "disabilitySpeaking": null,
  "disabilityHearing": null,
  "disabilityVision": null,
  "disabilityEliminating": null,
  "disabilityMental": null,
  "disabilityIndependentLiving": null,
  "disabilityTherapy": null,
  "yearImpaired": null,
  "devicesTherapy": null,
  "aiSummary": "A 1-2 sentence summary of this appointment"
}"""


def processAppointmentNote(
    clinicalNote: str,
    patient,
    physicianInfo: Dict,
) -> Dict:
    """
    Process a doctor's clinical note — extract patient field updates using LLM.

    Args:
        clinicalNote: Doctor's free-text note from the appointment
        patient: Patient model object
        physicianInfo: Dict with physician name, license, clinic info

    Returns: {
        "fieldUpdates": {...},   # Extracted fields to update
        "aiSummary": str,         # 1-2 sentence summary
        "redactionPreview": str,  # What the LLM saw
        "llmUsed": bool,
        "rawResponse": str,       # Raw LLM response (for debugging)
    }
    """
    from datetime import date
    today = date.today().isoformat()
    todayLong = date.today().strftime("%B %d, %Y")

    # ─── Step 1: Redact PII from the clinical note ───────────
    # Only redact identifiers (Tier 1) — medical data (diagnosis, meds, notes)
    # is NOT PII and is needed for the LLM to extract field updates
    noteRedaction = redactPii(clinicalNote, redactMedical=False)
    redactedNote = noteRedaction.redactedText

    # Also build redacted patient context
    patientContext, patientRedaction, fieldsIncluded, taskType = buildRedactedContext(
        patient, "process appointment note"
    )

    mergedTokens = {}
    mergedTokens.update(noteRedaction.tokenMap)
    mergedTokens.update(patientRedaction.tokenMap)

    logger.info(
        f"Appointment processing: patient={patient.patientName}, "
        f"note_tokens={len(noteRedaction.tokenMap)}, "
        f"patient_tokens={len(patientRedaction.tokenMap)}"
    )

    # ─── Step 2: Build LLM messages ──────────────────────────
    physicianContext = f"""Current Date: {todayLong} (ISO: {today})
Physician: {physicianInfo.get('physicianName', 'N/A')}"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": physicianContext},
        {"role": "system", "content": f"Patient Context (PII redacted):\n{patientContext}"},
        {"role": "user", "content": f"Extract patient field updates from this clinical note:\n\n{redactedNote}"},
    ]

    # ─── Step 3: Check LLM availability ─────────────────────
    if not llmClient.available:
        return {
            "fieldUpdates": {},
            "aiSummary": "LLM not available — note saved without AI extraction.",
            "redactionPreview": redactedNote,
            "llmUsed": False,
            "rawResponse": "",
        }

    # ─── Step 4: Call LLM ────────────────────────────────────
    response = llmClient.complete(
        prompt=f"Extract patient field updates from this clinical note:\n\n{redactedNote}",
        systemPrompt="\n\n".join(m["content"] for m in messages[:-1]),
        maxTokens=4096,
        temperature=0.2,
    )

    if not response:
        return {
            "fieldUpdates": {},
            "aiSummary": "LLM returned no response — note saved without AI extraction.",
            "redactionPreview": redactedNote,
            "llmUsed": False,
            "rawResponse": "",
        }

    # ─── Step 5: Parse JSON ──────────────────────────────────
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    if cleaned.startswith("json"):
        cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        extracted = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Appointment JSON parse failed: {e}")
        return {
            "fieldUpdates": {},
            "aiSummary": "AI extraction failed — note saved as-is.",
            "redactionPreview": redactedNote,
            "llmUsed": True,
            "rawResponse": response[:500],
        }

    # ─── Step 6: Restore PII tokens ──────────────────────────
    if mergedTokens and extracted:
        def restoreInObj(obj):
            if isinstance(obj, str):
                for token, original in mergedTokens.items():
                    if token in obj:
                        obj = obj.replace(token, original)
                return obj
            elif isinstance(obj, dict):
                return {k: restoreInObj(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [restoreInObj(item) for item in obj]
            return obj
        extracted = restoreInObj(extracted)

    # ─── Step 7: Separate field updates from summary ─────────
    aiSummary = extracted.pop("aiSummary", "Appointment processed.")
    fieldUpdates = {k: v for k, v in extracted.items() if v is not None}

    logger.info(f"Appointment processed: {len(fieldUpdates)} fields extracted, summary={aiSummary[:80]}")

    return {
        "fieldUpdates": fieldUpdates,
        "aiSummary": aiSummary,
        "redactionPreview": redactedNote,
        "llmUsed": True,
        "rawResponse": "",
    }


def applyFieldUpdates(patient, fieldUpdates: Dict) -> Tuple[Dict, Dict]:
    """
    Apply extracted field updates to the patient record.
    Returns (appliedFields, skippedFields) for the doctor to review.

    Only applies fields that are in the allowed list — prevents the LLM
    from writing to fields it shouldn't touch.
    """
    allowedFields = {
        "diagnosis", "medications", "allergies", "notes",
        "disabilityWalking", "disabilityDressing", "disabilityFeeding",
        "disabilitySpeaking", "disabilityHearing", "disabilityVision",
        "disabilityEliminating", "disabilityMental",
        "disabilityIndependentLiving", "disabilityTherapy",
        "yearImpaired", "devicesTherapy",
    }

    applied = {}
    skipped = {}

    for field, value in fieldUpdates.items():
        if field in allowedFields:
            oldValue = getattr(patient, field, None)
            setattr(patient, field, value)
            applied[field] = {"old": str(oldValue), "new": str(value)}
        else:
            skipped[field] = value

    return applied, skipped
