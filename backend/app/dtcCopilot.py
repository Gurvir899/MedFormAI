"""
DTC T2201 Copilot — generates a filled Disability Tax Credit form from clinical data.

Chunked into 5 small LLM calls (each < 1000 chars spec), all under token limits:
  Chunk 1: Part A (individual's section)
  Chunk 2: Walking category (most common DTC impairment)
  Chunk 3: Dressing category
  Chunk 4: Other categories (vision, speaking, hearing, eliminating, feeding, mental, cumulative, LST)
  Chunk 5: Certification

Flow:
  1. Load patient clinical record
  2. REDACT all PII → tokens
  3. Call LLM 5 times (small chunks), each returns JSON
  4. Merge all 5 JSON chunks into one complete form
  5. Restore PII tokens
  6. Fill physician info for certification
  7. Validate + return
"""

import json
import logging
from typing import Dict, Optional

from app.llmClient import llmClient
from app.encryption.piiScrubber import redactPii, restorePii, buildRedactedContext

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a medical form assistant helping a physician complete the CRA Disability Tax Credit Certificate (T2201).

Given the patient's clinical context (PII redacted), write a comprehensive narrative document that covers ALL sections of the T2201 form. Write it as a professional medical letter/document that a physician can review, edit, and then convert to PDF.

Format as markdown:
- Use ## headers for each section (Part A, Part B, Certification)
- Use **bold** for field labels
- Use bullet points for multiple values
- Write narrative paragraphs for the impairment examples
- Only include impairment categories where the patient has documented limitations
- Set fields you cannot determine to "—" or "N/A"
- Use the physician info from the Physician Context for certification fields

The document should read like a completed form rendered as a letter — not a JSON object, not a table. Each section flows naturally with the patient's information filled in.

Eligibility routes (the patient must meet at least one):
- Route A: Marked restriction in one category (unable or takes 3× longer, 90%+ of the time)
- Route B: Cumulative effect of significant limitations in 2+ categories
- Route C: Life-sustaining therapy (2+ times/week, 14+ hours/week)
All routes require the impairment to last 12+ continuous months."""

CHUNK_PART_A = """Write Part A — Individual's Section of the T2201 as a narrative document section.

Include:
- **Patient Name**: (from context)
- **SIN**: (from context or N/A)
- **Date of Birth**: (from context)
- **Mailing Address**: (from context)
- **Adjustments**: Is the applicant the person with the disability or their legal representative? Will they adjust previous tax returns?
- **Authorization**: Signature status (unsigned — patient signs later), telephone, date

Format as markdown with ## Part A header."""

CHUNK_WALKING = """Fill the Walking impairment category. Respond with JSON only. Set null if patient has no walking impairment.
{
  "partB": {
    "walking": { "designation": null, "q1Diagnoses": null, "q2Medication": null, "q3DevicesTherapy": null, "q4Examples": null, "q5MarkedRestriction": null, "q6AllOrSubstantiallyAll": null, "q7YearImpaired": null, "q8Prolonged12Months": null, "q9LikelyToImprove": null }
  }
}
designation: medicalDoctor. q4Examples: 2-3 sentence narrative. q5MarkedRestriction (bool): unable or takes 3x longer. q6AllOrSubstantiallyAll (bool): 90%+ of time. q8Prolonged12Months (bool). q9LikelyToImprove: yes/no/unsure."""

CHUNK_DRESSING = """Fill the Dressing impairment category. Respond with JSON only. Set null if no dressing impairment.
{
  "partB": {
    "dressing": { "designation": null, "q1Diagnoses": null, "q2Medication": null, "q3DevicesTherapy": null, "q4Examples": null, "q5MarkedRestriction": null, "q6AllOrSubstantiallyAll": null, "q7YearImpaired": null, "q8Prolonged12Months": null, "q9LikelyToImprove": null }
  }
}
Same field structure as walking. designation: medicalDoctor. Set null if not applicable."""

CHUNK_OTHER_CATS = """Fill remaining Part B categories if applicable. Respond with JSON only. Set null for not applicable.
{
  "partB": {
    "vision": null,
    "speaking": null,
    "hearing": null,
    "eliminating": null,
    "feeding": null,
    "mentalFunctions": null,
    "cumulativeEffect": null,
    "lifeSustainingTherapy": null
  }
}"""

CHUNK_CERT = """Fill the Certification section. Respond with JSON only.
{
  "certification": {
    "certYearFrom": null, "certYearTo": null, "certHasMedicalInfoOnFile": null,
    "certPractitionerType": null, "certSignature": null, "certNamePrinted": null,
    "certLicenseNumber": null, "certTelephone": null, "certDate": null, "certAddress": null
  }
}
Use physician info from context. certSignature: "unsigned". certHasMedicalInfoOnFile: true. certPractitionerType: "medicalDoctor"."""


def _parseJsonResponse(response):
    if not response:
        return None
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    if cleaned.startswith("json"):
        cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}, response: {cleaned[:200]}")
        return None


def _restoreTokensInObj(obj, tokenMap):
    if isinstance(obj, str):
        for token, original in tokenMap.items():
            if token in obj:
                obj = obj.replace(token, original)
        return obj
    elif isinstance(obj, dict):
        return {k: _restoreTokensInObj(v, tokenMap) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_restoreTokensInObj(item, tokenMap) for item in obj]
    return obj


def _callChunk(spec, physicianContext, redactedContext):
    """Call LLM for one chunk and return parsed JSON."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": physicianContext},
        {"role": "system", "content": f"Patient Context (PII redacted):\n{redactedContext}"},
        {"role": "user", "content": spec},
    ]
    response = llmClient.complete(
        prompt=spec,
        systemPrompt="\n\n".join(m["content"] for m in messages[:-1]),
        maxTokens=4096,
        temperature=0.2,
    )
    if not response:
        return None
    return _parseJsonResponse(response)


def _deepMerge(base, update):
    """Deep merge two dicts — update into base."""
    for key, val in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            _deepMerge(base[key], val)
        else:
            base[key] = val
    return base


def generateDtcForm(patient, physicianInfo, userId):
    """
    Generate a filled T2201 form from patient clinical data using 5 small LLM calls.
    """
    from datetime import date
    today = date.today().isoformat()
    todayLong = date.today().strftime("%B %d, %Y")

    # Step 1: Build + redact clinical context
    redactedContext, redactionResult, fieldsIncluded, taskType = buildRedactedContext(
        patient, "fill DTC T2201 form for this patient"
    )
    queryRedaction = redactPii("Fill the DTC T2201 form for this patient")
    mergedTokens = {}
    mergedTokens.update(redactionResult.tokenMap)
    mergedTokens.update(queryRedaction.tokenMap)

    logger.info(f"DTC generation: patient={patient.patientName}, tokens={len(mergedTokens)}")

    # Build physician context
    physicianContext = f"""Current Date: {todayLong} (ISO: {today})
Physician Name: {physicianInfo.get('physicianName', 'N/A')}
Physician License: {physicianInfo.get('physicianLicense', 'N/A')}
Clinic Name: {physicianInfo.get('clinicName', 'N/A')}
Clinic Address: {physicianInfo.get('clinicAddress', 'N/A')}
Clinic Phone: {physicianInfo.get('clinicPhone', 'N/A')}"""

    if not llmClient.available:
        return {"formData": {}, "validation": {"passed": False, "errors": [{"rule": "LLM", "message": "LLM not available"}], "warnings": []}, "redactionPreview": redactedContext, "llmUsed": False}

    mergedFormData = {}
    chunks = [
        ("Part A", CHUNK_PART_A),
        ("Walking", CHUNK_WALKING),
        ("Dressing", CHUNK_DRESSING),
        ("Other categories", CHUNK_OTHER_CATS),
        ("Certification", CHUNK_CERT),
    ]

    succeeded = 0
    for chunkName, chunkSpec in chunks:
        logger.info(f"DTC chunk: {chunkName} — calling LLM...")
        chunkData = _callChunk(chunkSpec, physicianContext, redactedContext)
        if chunkData:
            _deepMerge(mergedFormData, chunkData)
            succeeded += 1
            logger.info(f"DTC chunk: {chunkName} — success")
        else:
            logger.warning(f"DTC chunk: {chunkName} — failed")

    # Restore PII tokens in LLM response
    if mergedTokens and mergedFormData:
        mergedFormData = _restoreTokensInObj(mergedFormData, mergedTokens)

    # ─── Fill Part A with actual patient data (LLM saw redacted tokens) ───
    partA = mergedFormData.get("partA", {})
    pwd = partA.get("personWithDisability", {})
    # Patient name — split into first/last
    fullName = patient.patientName or ""
    nameParts = fullName.split(" ", 1)
    pwd["personFirstName"] = pwd.get("personFirstName") or (nameParts[0] if nameParts else "")
    pwd["personLastName"] = pwd.get("personLastName") or (nameParts[1] if len(nameParts) > 1 else "")
    pwd["personDateOfBirth"] = pwd.get("personDateOfBirth") or getattr(patient, "dateOfBirth", "") or ""
    pwd["personSin"] = pwd.get("personSin") or getattr(patient, "sin", "") or ""
    pwd["personMailingAddress"] = pwd.get("personMailingAddress") or getattr(patient, "address", "") or ""
    pwd["personCity"] = pwd.get("personCity") or getattr(patient, "city", "") or ""
    pwd["personProvince"] = pwd.get("personProvince") or getattr(patient, "province", "") or ""
    pwd["personPostalCode"] = pwd.get("personPostalCode") or getattr(patient, "postalCode", "") or ""
    partA["personWithDisability"] = pwd

    # Adjustments — assume self unless clinical notes say otherwise
    adj = partA.get("adjustments", {})
    adj.setdefault("isSelfOrLegalRep", True)
    adj.setdefault("adjustPreviousReturns", "adjustAllApplicableYears")
    partA["adjustments"] = adj

    # Authorization — patient signs later
    auth = partA.get("authorization", {})
    auth.setdefault("partAQ4Signature", "unsigned")
    auth.setdefault("partAQ4Telephone", physicianInfo.get("clinicPhone", ""))
    auth.setdefault("partAQ4Date", today)
    partA["authorization"] = auth
    mergedFormData["partA"] = partA

    # Fill physician info for certification
    cert = mergedFormData.get("certification", {})
    cert.setdefault("certPractitionerType", "medicalDoctor")
    cert.setdefault("certNamePrinted", physicianInfo.get("physicianName", ""))
    cert.setdefault("certLicenseNumber", physicianInfo.get("physicianLicense", ""))
    cert.setdefault("certTelephone", physicianInfo.get("clinicPhone", ""))
    cert.setdefault("certAddress", physicianInfo.get("clinicAddress", ""))
    cert.setdefault("certDate", today)
    cert.setdefault("certSignature", "unsigned")
    cert.setdefault("certYearTo", today[:4])
    cert.setdefault("certHasMedicalInfoOnFile", True)
    mergedFormData["certification"] = cert

    # Fill patient name header
    partB = mergedFormData.get("partB", {})
    if not partB.get("patientNameHeader"):
        partA = mergedFormData.get("partA", {})
        pwd = partA.get("personWithDisability", {})
        firstName = pwd.get("personFirstName", "")
        lastName = pwd.get("personLastName", "")
        if firstName or lastName:
            partB["patientNameHeader"] = f"{firstName} {lastName}".strip()
    mergedFormData["partB"] = partB

    # Ensure structure
    mergedFormData.setdefault("partA", {})
    mergedFormData.setdefault("partB", {})
    mergedFormData.setdefault("certification", {})

    # Validate
    try:
        from schemas.dtcT2201Schema import validateDtcForm
        validation = validateDtcForm(mergedFormData)
    except ImportError:
        validation = {"passed": True, "errors": [], "warnings": [], "note": "Schema validation not available"}

    logger.info(f"DTC form generated: chunks={succeeded}/{len(chunks)}, validation={validation.get('passed')}")

    return {
        "formData": mergedFormData,
        "validation": validation,
        "redactionPreview": redactedContext,
        "llmUsed": succeeded == len(chunks),
    }
