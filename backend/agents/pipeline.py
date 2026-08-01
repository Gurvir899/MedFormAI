"""
Multi-agent pipeline orchestrator.

Coordinates the three agents:
  1. Data Extractor → pulls patient data from EMR
  2. Form Filler → maps data to form schema, uses LLM for narratives
  3. PII Guardian → scans final form for compliance

Usage:
    pipeline = FormAutomationPipeline()
    result = pipeline.processForm(patientId="123", formType="dtc")
"""

import logging
from typing import Dict, Optional

from agents.dataExtractor import DataExtractor
from agents.formFiller import FormFiller
from agents.piiGuardian import PiiGuardian

logger = logging.getLogger(__name__)


class FormAutomationPipeline:
    """
    Orchestrates the three-agent pipeline for medical form automation.

    Data flows: EMR → Agent 1 (Extract) → Agent 2 (Fill) → Agent 3 (Scan) → Output
    """

    def __init__(self, llmClient=None, emrEndpoint: Optional[str] = None,
                 emrApiKey: Optional[str] = None):
        self.dataExtractor = DataExtractor(emrEndpoint=emrEndpoint, emrApiKey=emrApiKey)
        self.formFiller = FormFiller(llmClient=llmClient)
        self.piiGuardian = PiiGuardian()

    def processForm(self, patientId: str, formType: str = "dtc",
                    physicianId: Optional[str] = None) -> Dict:
        """
        Run the full pipeline: extract → fill → scan.

        Returns comprehensive result with form data, compliance report,
        and metadata for audit trail.
        """
        pipelineSteps = []

        # ─── Agent 1: Extract ─────────────────────────────────
        logger.info(f"Pipeline: Step 1 — Data extraction for patient {patientId}")
        patientData = self.dataExtractor.extractPatientData(patientId)
        pipelineSteps.append({
            "agent": "dataExtractor",
            "status": "completed",
            "fieldsExtracted": len(patientData),
        })

        # ─── Agent 2: Fill ────────────────────────────────────
        logger.info(f"Pipeline: Step 2 — Form filling for {formType}")
        fillResult = self.formFiller.fillForm(patientData, formType)
        pipelineSteps.append({
            "agent": "formFiller",
            "status": "completed",
            "fieldsPopulated": len(fillResult["formData"]),
            "requiresReview": fillResult["requiresReview"],
            "avgConfidence": (
                sum(fillResult["confidence"].values()) / max(1, len(fillResult["confidence"]))
            ),
        })

        # ─── Agent 3: PII Scan ────────────────────────────────
        logger.info(f"Pipeline: Step 3 — PII compliance scan")
        scanResult = self.piiGuardian.scanFormSubmission(
            formData=fillResult["formData"],
            formType=formType,
        )
        pipelineSteps.append({
            "agent": "piiGuardian",
            "status": "completed",
            "passed": scanResult["passed"],
            "complianceScore": scanResult["score"],
            "findingsCount": len(scanResult["findings"]),
        })

        return {
            "formType": formType,
            "patientId": patientId,
            "physicianId": physicianId,
            "formData": fillResult["formData"],
            "confidence": fillResult["confidence"],
            "requiresReview": fillResult["requiresReview"],
            "piiScan": scanResult,
            "pipelineSteps": pipelineSteps,
            "redactedPreview": scanResult["redactedPreview"],
        }
