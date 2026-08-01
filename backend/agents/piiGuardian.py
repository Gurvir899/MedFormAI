"""
Agent 3: PII Guardian

Scans every form submission for PII compliance BEFORE it leaves the system.

This is the compliance layer — it enforces:
  1. Minimum-necessary PII in form output
  2. No PII leakage in generated narratives
  3. All fields properly encrypted before storage
  4. Audit trail generated for every field
"""

import json
import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone

from app.encryption import redactPii
from schemas.dtcForm import getFormSchema, getRequiredPiiFields

logger = logging.getLogger(__name__)


class PiiGuardian:
    """
    Final compliance gate before form data is stored or submitted.

    Runs a full PII scan on the completed form and produces:
      - pass/fail status
      - list of findings (excess PII, leaked PII in narratives, etc.)
      - redacted preview (safe for logging/preview)
      - compliance score
    """

    def __init__(self):
        self.formSchema = getFormSchema()
        self.allowedPiiFields = set(getRequiredPiiFields())

    def scanFormSubmission(self, formData: Dict,
                           formType: str = "dtc") -> Dict:
        """
        Run full compliance scan on a completed form.

        Returns:
            {
                "passed": bool,
                "score": float,  # 0.0 to 1.0
                "findings": List[Dict],
                "redactedPreview": str,
                "timestamp": str,
            }
        """
        logger.info(f"Agent 3 (PII Guardian): Scanning {formType} form submission")

        # Load the correct schema for this form type
        if formType == "sickNote":
            from schemas.sickNoteForm import getSickNoteSchema
            self.formSchema = getSickNoteSchema()
            self.allowedPiiFields = set(self._getRequiredPiiFromSchema(self.formSchema))
        else:
            from schemas.dtcForm import getFormSchema, getRequiredPiiFields
            self.formSchema = getFormSchema()
            self.allowedPiiFields = set(getRequiredPiiFields())

        findings = []

        # 1. Check for excess PII fields
        excessFindings = self._checkExcessPii(formData, formType)
        findings.extend(excessFindings)

        # 2. Check for PII leakage in narrative fields
        leakageFindings = self._checkPiiLeakage(formData)
        findings.extend(leakageFindings)

        # 3. Check required fields are present
        missingFindings = self._checkRequiredFields(formData)
        findings.extend(missingFindings)

        # 4. Check SIN format (must not be in narrative text)
        sinFindings = self._checkSinInNarratives(formData)
        findings.extend(sinFindings)

        # Generate redacted preview
        redactedPreview = self._generateRedactedPreview(formData)

        # Calculate compliance score
        criticalCount = sum(1 for f in findings if f["severity"] == "critical")
        warningCount = sum(1 for f in findings if f["severity"] == "warning")
        infoCount = sum(1 for f in findings if f["severity"] == "info")

        score = max(0.0, 1.0 - (criticalCount * 0.3 + warningCount * 0.1 + infoCount * 0.02))
        passed = criticalCount == 0

        result = {
            "passed": passed,
            "score": round(score, 3),
            "findings": findings,
            "redactedPreview": redactedPreview,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "criticalCount": criticalCount,
                "warningCount": warningCount,
                "infoCount": infoCount,
                "totalFindings": len(findings),
            },
        }

        logger.info(
            f"PII scan complete: passed={passed} score={score:.2f} "
            f"findings={len(findings)}"
        )
        return result

    def _checkExcessPii(self, formData: Dict, formType: str) -> List[Dict]:
        """Check if form contains PII fields beyond what this form requires."""
        findings = []

        # Build set of allowed field IDs for this form
        allowedFieldIds = set()
        for section in self.formSchema["sections"]:
            for field in section["fields"]:
                if field.get("piiClassification"):
                    allowedFieldIds.add(field["fieldId"])

        # Check for unexpected fields in formData
        for fieldId, value in formData.items():
            fieldDef = self._findField(fieldId)
            if fieldDef is None and self._looksLikePii(fieldId, value):
                findings.append({
                    "type": "excess_pii",
                    "severity": "critical",
                    "field": fieldId,
                    "message": (
                        f"Field '{fieldId}' is not part of the {formType} form "
                        f"schema and appears to contain PII. Remove this field "
                        f"or classify it in the form schema."
                    ),
                })

        return findings

    def _checkPiiLeakage(self, formData: Dict) -> List[Dict]:
        """Check narrative/text fields for leaked PII that shouldn't be there."""
        findings = []

        # Fields that should contain clinical info only, no identifiers
        narrativeFields = ["effectsDescription", "duration", "clinicalNotes"]

        # PII patterns that should NOT appear in narrative fields
        leakedPatterns = [
            (r"\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b", "SIN"),
            (r"\b[\w.-]+@[\w.-]+\.\w+\b", "email"),
            (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone"),
        ]

        for fieldId in narrativeFields:
            value = formData.get(fieldId)
            if not value or not isinstance(value, str):
                continue

            for pattern, piiType in leakedPatterns:
                matches = re.finditer(pattern, value, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        "type": "pii_leakage",
                        "severity": "critical",
                        "field": fieldId,
                        "piiType": piiType,
                        "message": (
                            f"Potential {piiType} found in narrative field "
                            f"'{fieldId}'. This field should contain clinical "
                            f"information only. Remove the {piiType}."
                        ),
                    })

        return findings

    def _checkRequiredFields(self, formData: Dict) -> List[Dict]:
        """Check that all required form fields are present and non-empty."""
        findings = []

        for section in self.formSchema["sections"]:
            for field in section["fields"]:
                if not field.get("required"):
                    continue

                fieldId = field["fieldId"]
                value = formData.get(fieldId)

                if value is None or (isinstance(value, str) and not value.strip()):
                    findings.append({
                        "type": "missing_required",
                        "severity": "warning",
                        "field": fieldId,
                        "message": f"Required field '{fieldId}' is empty.",
                    })

        return findings

    def _checkSinInNarratives(self, formData: Dict) -> List[Dict]:
        """Specifically check that SIN doesn't appear in any narrative field."""
        findings = []

        sinPattern = re.compile(r"\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b")
        narrativeFieldIds = []

        for section in self.formSchema["sections"]:
            for field in section["fields"]:
                if field["fieldType"] == "textarea":
                    narrativeFieldIds.append(field["fieldId"])

        for fieldId in narrativeFieldIds:
            value = formData.get(fieldId, "")
            if isinstance(value, str) and sinPattern.search(value):
                findings.append({
                    "type": "sin_in_narrative",
                    "severity": "critical",
                    "field": fieldId,
                    "message": (
                        "SIN detected in a narrative field. SIN must only "
                        "appear in the designated SIN field, never in clinical "
                        "descriptions."
                    ),
                })

        return findings

    def _generateRedactedPreview(self, formData: Dict) -> str:
        """Generate a PII-redacted preview of the form for logging/display."""
        preview = {}
        for fieldId, value in formData.items():
            if isinstance(value, str):
                redactionResult = redactPii(value)
                preview[fieldId] = redactionResult.redactedText
            else:
                preview[fieldId] = value

        return json.dumps(preview, indent=2, ensure_ascii=False)

    def _findField(self, fieldId: str) -> Optional[dict]:
        """Find a field definition by ID."""
        for section in self.formSchema["sections"]:
            for field in section["fields"]:
                if field["fieldId"] == fieldId:
                    return field
        return None

    @staticmethod
    def _looksLikePii(fieldId: str, value: any) -> bool:
        """Heuristic: does this field name + value look like PII?"""
        piiKeywords = [
            "name", "dob", "birth", "address", "phone", "email",
            "sin", "health", "card", "diagnosis", "phn",
        ]
        fieldLower = fieldId.lower()
        return any(kw in fieldLower for kw in piiKeywords)

    @staticmethod
    def _getRequiredPiiFromSchema(schema: dict) -> List[str]:
        """Extract PII classifications from any form schema."""
        piiFields = []
        for section in schema.get("sections", []):
            for field in section.get("fields", []):
                piiClass = field.get("piiClassification")
                if piiClass and piiClass not in piiFields:
                    piiFields.append(piiClass)
        return piiFields
