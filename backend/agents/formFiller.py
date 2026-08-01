"""
Agent 2: Form Filler

Maps extracted clinical data onto the DTC form schema.

Uses an LLM to generate narrative descriptions where clinical judgment
is needed (e.g., "describe effects of impairment on daily activities"),
but all PII is redacted BEFORE sending to the LLM.
"""

import json
import logging
from typing import Dict, Optional

from app.encryption import redactPii, restorePii
from schemas.dtcForm import getFormSchema

logger = logging.getLogger(__name__)


class FormFiller:
    """
    Auto-populates form fields from extracted patient data.

    Flow:
      1. Match EMR data fields → form field schema
      2. Direct-fill fields (name, DOB, address — straightforward mapping)
      3. LLM-generated fields (narrative descriptions) — PII redacted first
      4. Return populated form with confidence scores
    """

    def __init__(self, llmClient=None):
        self.llmClient = llmClient
        self.formSchema = getFormSchema()

    def fillForm(self, patientData: Dict, formType: str = "dtc") -> Dict:
        """
        Main entry: populate form fields from patient data.

        Returns:
            {
                "formType": "dtc",
                "formData": { fieldId: value, ... },
                "confidence": { fieldId: score, ... },
                "piiRedactionMap": { token: original, ... },
                "requiresReview": bool
            }
        """
        logger.info(f"Agent 2 (Form Filler): Populating {formType} form")

        formData = {}
        confidence = {}
        redactionMap = {}

        for section in self.formSchema["sections"]:
            for field in section["fields"]:
                fieldId = field["fieldId"]
                emrSource = field.get("emrSource")

                if not emrSource:
                    # Non-data fields like dateOfCertification
                    if fieldId == "dateOfCertification":
                        from datetime import date
                        formData[fieldId] = date.today().isoformat()
                        confidence[fieldId] = 1.0
                    continue

                # Resolve emrSource path (e.g., "patient.patientName")
                value = self._resolvePath(patientData, emrSource)

                if value is None:
                    confidence[fieldId] = 0.0
                    continue

                # Direct-fill fields
                if field["fieldType"] in ("text", "date", "textarea", "number"):
                    formData[fieldId] = value
                    confidence[fieldId] = 0.95

                # Checkbox/radio — needs LLM classification
                elif field["fieldType"] in ("checkbox", "radio"):
                    if self.llmClient:
                        llmResult = self._llmClassify(field, value, redactionMap)
                        formData[fieldId] = llmResult["value"]
                        confidence[fieldId] = llmResult["confidence"]
                    else:
                        formData[fieldId] = value
                        confidence[fieldId] = 0.6

        # Generate narrative descriptions using LLM (if available)
        narrativeFields = [
            ("effectsDescription", "clinicalNotes"),
            ("duration", "prognosis"),
        ]

        for formField, dataSource in narrativeFields:
            if formField not in formData or not formData[formField]:
                sourceValue = patientData.get(dataSource, "")
                if sourceValue and self.llmClient:
                    llmResult = self._llmGenerateNarrative(
                        formField, sourceValue, redactionMap
                    )
                    if llmResult:
                        formData[formField] = llmResult["value"]
                        confidence[formField] = llmResult["confidence"]

        requiresReview = any(c < 0.8 for c in confidence.values())

        return {
            "formType": formType,
            "formData": formData,
            "confidence": confidence,
            "piiRedactionMap": redactionMap,
            "requiresReview": requiresReview,
        }

    def _resolvePath(self, data: Dict, path: str) -> Optional[object]:
        """Resolve a dot-notation path in a nested dict."""
        parts = path.replace("patient.", "").replace("physician.", "").split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    def _llmClassify(self, field: dict, value: str,
                     redactionMap: Dict) -> Dict:
        """Use LLM to classify a value into checkbox/radio options."""
        prompt = (
            f"Given the patient clinical data: '{value}', "
            f"classify which of these options apply: "
            f"{field.get('helpText', field['label'])}. "
            f"Respond with only the classification value."
        )

        # REDACT PII before LLM call
        redactionResult = redactPii(prompt)
        redactedPrompt = redactionResult.redactedText
        redactionMap.update(redactionResult.tokenMap)

        response = self._callLlm(redactedPrompt)

        # RESTORE PII after LLM response
        if response:
            response = restorePii(response, redactionResult.tokenMap)

        return {
            "value": response or value,
            "confidence": 0.75 if response else 0.4,
        }

    def _llmGenerateNarrative(self, fieldId: str, sourceValue: str,
                              redactionMap: Dict) -> Optional[Dict]:
        """Generate narrative text using LLM, with PII redaction."""
        fieldDef = self._findField(fieldId)
        if not fieldDef:
            return None

        prompt = (
            f"You are a medical practitioner completing the Disability Tax Credit form. "
            f"Field: {fieldDef['label']}\n"
            f"Patient clinical notes: '{sourceValue}'\n"
            f"Write a concise, factual response for this form field. "
            f"Do not include patient name, DOB, or identifying information. "
            f"Focus on clinical facts only."
        )

        # REDACT before LLM
        redactionResult = redactPii(prompt)
        redactedPrompt = redactionResult.redactedText
        redactionMap.update(redactionResult.tokenMap)

        response = self._callLlm(redactedPrompt)

        return {
            "value": response,
            "confidence": 0.8 if response else 0.0,
        }

    def _findField(self, fieldId: str) -> Optional[dict]:
        """Find a field definition by ID in the form schema."""
        for section in self.formSchema["sections"]:
            for field in section["fields"]:
                if field["fieldId"] == fieldId:
                    return field
        return None

    def _callLlm(self, prompt: str) -> Optional[str]:
        """Call the configured LLM API. Returns None if unavailable."""
        if not self.llmClient:
            return None

        try:
            response = self.llmClient.chat.completions.create(
                model=self.llmClient.modelName,
                messages=[{"role": "user", "content": prompt}],
                maxTokens=500,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None
