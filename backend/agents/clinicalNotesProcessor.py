"""
Clinical Notes Processor — the real engine.

Doctor pastes raw clinical notes → system extracts relevant info → 
fills form fields → PII scan → downloadable output.

This is what makes Paean actually DO something instead of being a showcase.

Two modes:
  1. "Fill from notes" — doctor pastes clinical notes, system fills form
  2. "Generate sick note" — doctor describes visit, system generates complete sick note

Both go through:
  clinical notes → LLM (PII redacted) → form fields → PII scan → output
"""

import json
import logging
from datetime import date, datetime
from typing import Dict, Optional, List

from app.llmClient import llmClient
from app.encryption import redactPii, restorePii
from app.encryption.piiScrubber import RedactionResult
from agents.piiGuardian import PiiGuardian

logger = logging.getLogger(__name__)


class ClinicalNotesProcessor:
    """
    Takes raw clinical notes from a doctor and produces a filled medical form.
    
    The flow:
      1. Doctor writes clinical notes (free text, like they already do)
      2. We redact all PII → tokens
      3. Redacted notes go to LLM with form-specific extraction prompt
      4. LLM returns structured form fields (no real PII, just tokens)
      5. We restore PII from token map
      6. PII Guardian scans the final form
      7. Output: filled form + compliance report + time saved
    """

    def __init__(self):
        self.piiGuardian = PiiGuardian()

    def processClinicalNotes(
        self,
        clinicalNotes: str,
        formType: str = "sickNote",
        physicianName: str = "",
        physicianLicense: str = "",
        clinicName: str = "",
        clinicAddress: str = "",
    ) -> Dict:
        """
        Main entry point. Takes raw clinical notes → filled form.
        
        Args:
            clinicalNotes: Raw notes from doctor's visit (free text)
            formType: "sickNote" or "dtc"
            physicianName: Dr. name for form signature
            physicianLicense: License number
            clinicName: Clinic name
            clinicAddress: Clinic address
            
        Returns:
            {
                "formType": str,
                "formData": dict,           # Filled form fields
                "piiScan": dict,             # Compliance scan results
                "timeSavedMinutes": float,   # Estimated time saved
                "manualTimeMinutes": float,  # How long this would take manually
                "originalNotes": str,        # What doctor wrote
                "redactedNotesPreview": str,  # What LLM saw (PII redacted)
                "llmUsed": bool,             # Whether LLM was available
            }
        """
        logger.info(f"Processing clinical notes for {formType} form")

        # ─── Step 1: Redact PII from clinical notes ──────────
        redactionResult = redactPii(clinicalNotes)
        redactedNotes = redactionResult.redactedText
        
        logger.info(f"Redacted {len(redactionResult.tokenMap)} PII tokens from clinical notes")

        # ─── Step 2: Generate form fields using LLM ──────────
        if formType == "sickNote":
            formData, llmUsed = self._generateSickNote(
                redactedNotes, redactionResult,
                physicianName, physicianLicense,
                clinicName, clinicAddress,
            )
            manualTimeMin = 10.4  # From CMA report
        elif formType == "dtc":
            formData, llmUsed = self._generateDtc(
                redactedNotes, redactionResult,
                physicianName, physicianLicense,
                clinicName, clinicAddress,
            )
            manualTimeMin = 36.6  # From CMA report
        else:
            return {"error": f"Unknown form type: {formType}"}

        # ─── Step 3: PII Guardian scan ────────────────────────
        piiScan = self.piiGuardian.scanFormSubmission(formData, formType)

        # ─── Step 4: Calculate time saved ────────────────────
        # Automated takes ~2 min of doctor review vs manual completion
        automatedTimeMin = 2.0
        timeSavedMin = max(0, manualTimeMin - automatedTimeMin)

        return {
            "formType": formType,
            "formData": formData,
            "piiScan": piiScan,
            "timeSavedMinutes": round(timeSavedMin, 1),
            "manualTimeMinutes": manualTimeMin,
            "automatedTimeMinutes": automatedTimeMin,
            "originalNotes": clinicalNotes,
            "redactedNotesPreview": redactedNotes,
            "llmUsed": llmUsed,
            "timestamp": datetime.now().isoformat(),
        }

    def _generateSickNote(
        self,
        redactedNotes: str,
        redactionResult: RedactionResult,
        physicianName: str,
        physicianLicense: str,
        clinicName: str,
        clinicAddress: str,
    ) -> tuple[Dict, bool]:
        """Generate a sick note from clinical notes using LLM."""

        today = date.today().isoformat()

        # Default form data (filled without LLM)
        formData = {
            "patientName": "",  # Will be restored from tokens
            "dateOfBirth": "",
            "assessmentDate": today,
            "reasonForAbsence": "",
            "startDate": today,
            "expectedReturnDate": "",
            "fitnessForDuty": "",
            "physicianName": physicianName,
            "physicianLicense": physicianLicense,
            "clinicName": clinicName,
            "clinicAddress": clinicAddress,
            "dateOfIssue": today,
        }

        llmUsed = False

        if llmClient.available:
            # ─── LLM prompt (PII already redacted) ─────────
            systemPrompt = (
                "You are a medical form assistant. You help physicians complete "
                "sick leave certificates from their clinical notes. "
                "Extract ONLY the medically relevant information needed for the form. "
                "Do NOT include patient names, DOBs, or identifying details in your "
                "response — these will be inserted separately. "
                "Respond in JSON format with these exact keys: "
                "reasonForAbsence, startDate, expectedReturnDate, fitnessForDuty. "
                "For fitnessForDuty, write a professional statement like: "
                "'Patient is medically unfit for work/school from [start] to [end].'"
            )

            userPrompt = (
                f"Clinical notes (PII redacted):\n{redactedNotes}\n\n"
                f"Extract the information needed for a sick leave certificate. "
                f"Respond as JSON with keys: reasonForAbsence, startDate, "
                f"expectedReturnDate, fitnessForDuty."
            )

            response = llmClient.complete(
                prompt=userPrompt,
                systemPrompt=systemPrompt,
                maxTokens=4096,
                temperature=0.2,
            )

            if response:
                llmUsed = True
                # Parse LLM JSON response
                try:
                    # Strip markdown code fences if present
                    cleaned = response.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()

                    llmFields = json.loads(cleaned)
                    formData["reasonForAbsence"] = llmFields.get("reasonForAbsence", "")
                    formData["startDate"] = llmFields.get("startDate", today)
                    formData["expectedReturnDate"] = llmFields.get("expectedReturnDate", "")
                    formData["fitnessForDuty"] = llmFields.get("fitnessForDuty", "")
                except json.JSONDecodeError:
                    # If JSON parse fails, use raw response as reason
                    formData["reasonForAbsence"] = response[:500]
                    formData["fitnessForDuty"] = (
                        f"Patient is medically unfit for work/school "
                        f"from {today} until further evaluation."
                    )

        # ─── Restore PII from token map ─────────────────
        # Extract patient name and DOB from the redaction map
        for token, originalValue in redactionResult.tokenMap.items():
            if "PATIENT_NAME" in token:
                formData["patientName"] = originalValue
            elif "DOB" in token:
                formData["dateOfBirth"] = originalValue

        # If no patient name was captured via redaction, check raw notes
        if not formData["patientName"]:
            import re
            nameMatch = re.search(r'\bPatient:\s*([A-Z][a-z]+ [A-Z][a-z]+)', redactionResult.redactedText)
            if nameMatch:
                # Already redacted — restore from map
                pass  # Token-based restore above should have caught it

        return formData, llmUsed

    def _generateDtc(
        self,
        redactedNotes: str,
        redactionResult: RedactionResult,
        physicianName: str,
        physicianLicense: str,
        clinicName: str,
        clinicAddress: str,
    ) -> tuple[Dict, bool]:
        """Generate DTC form fields from clinical notes using LLM."""

        today = date.today().isoformat()

        formData = {
            "patientName": "",
            "dateOfBirth": "",
            "sin": "",
            "address": "",
            "phoneNumber": "",
            "impairmentType": "",
            "onsetDate": "",
            "effectsDescription": "",
            "duration": "",
            "lifeSustainingTherapy": "",
            "therapyFrequency": "",
            "physicianName": physicianName,
            "physicianLicense": physicianLicense,
            "clinicAddress": clinicAddress,
            "dateOfCertification": today,
        }

        llmUsed = False

        if llmClient.available:
            systemPrompt = (
                "You are a medical form assistant helping a physician complete "
                "the Disability Tax Credit Certificate (T2201). "
                "Extract relevant clinical information from the notes. "
                "Do NOT include patient names, DOBs, SINs, or contact details — "
                "those are handled separately. "
                "Respond in JSON format with these exact keys: "
                "impairmentType, onsetDate, effectsDescription, duration, "
                "lifeSustainingTherapy, therapyFrequency. "
                "For effectsDescription, write 2-3 sentences describing how "
                "the impairment affects daily activities. "
                "For duration, state whether it's prolonged (12+ months)."
            )

            userPrompt = (
                f"Clinical notes (PII redacted):\n{redactedNotes}\n\n"
                f"Extract information for the DTC form. Respond as JSON."
            )

            response = llmClient.complete(
                prompt=userPrompt,
                systemPrompt=systemPrompt,
                maxTokens=4096,
                temperature=0.2,
            )

            if response:
                llmUsed = True
                try:
                    cleaned = response.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()

                    llmFields = json.loads(cleaned)
                    formData["impairmentType"] = llmFields.get("impairmentType", "")
                    formData["onsetDate"] = llmFields.get("onsetDate", "")
                    formData["effectsDescription"] = llmFields.get("effectsDescription", "")
                    formData["duration"] = llmFields.get("duration", "")
                    formData["lifeSustainingTherapy"] = llmFields.get("lifeSustainingTherapy", "")
                    formData["therapyFrequency"] = llmFields.get("therapyFrequency", "")
                except json.JSONDecodeError:
                    formData["effectsDescription"] = response[:500]
                    formData["duration"] = "Prolonged — expected to last 12+ months"

        # Restore PII from token map
        for token, originalValue in redactionResult.tokenMap.items():
            if "PATIENT_NAME" in token:
                formData["patientName"] = originalValue
            elif "DOB" in token:
                formData["dateOfBirth"] = originalValue
            elif "SIN" in token:
                formData["sin"] = originalValue
            elif "ADDRESS" in token:
                formData["address"] = originalValue
            elif "PHONE" in token:
                formData["phoneNumber"] = originalValue

        return formData, llmUsed
