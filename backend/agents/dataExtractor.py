"""
Agent 1: Data Extractor

Pulls patient clinical data from EMR and structures it for form filling.

In production, this would connect to EMR systems via HL7 FHIR APIs.
For the prototype, we simulate EMR data retrieval with realistic structure.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Extracts patient data from EMR systems.

    Production: HL7 FHIR R4 API calls
    Prototype: Simulated EMR data for demo purposes
    """

    def __init__(self, emrEndpoint: Optional[str] = None,
                 emrApiKey: Optional[str] = None):
        self.emrEndpoint = emrEndpoint
        self.emrApiKey = emrApiKey

    def extractPatientData(self, patientId: str) -> Dict:
        """
        Retrieve patient clinical data from EMR.

        In production:
            GET {emrEndpoint}/Patient/{patientId}
            GET {emrEndpoint}/Condition?patient={patientId}
            GET {emrEndpoint}/MedicationRequest?patient={patientId}

        Returns structured patient data for form filling.
        """
        logger.info(f"Agent 1 (Data Extractor): Retrieving data for patient {patientId}")

        if self.emrEndpoint:
            # Production: real FHIR API call
            return self._fetchFromFhir(patientId)
        else:
            # Prototype: simulated EMR data
            return self._simulateEmrData(patientId)

    def _fetchFromFhir(self, patientId: str) -> Dict:
        """Fetch real patient data from FHIR R4 endpoint."""
        import requests

        headers = {
            "Authorization": f"Bearer {self.emrApiKey}",
            "Accept": "application/fhir+json",
        }

        try:
            # Fetch Patient resource
            resp = requests.get(
                f"{self.emrEndpoint}/Patient/{patientId}",
                headers=headers,
                timeout=10,
            )
            resp.raiseForStatus()
            patientResource = resp.json()

            # Fetch Conditions (diagnoses)
            resp = requests.get(
                f"{self.emrEndpoint}/Condition",
                headers=headers,
                params={"patient": patientId},
                timeout=10,
            )
            conditions = resp.json().get("entry", [])

            return self._normalizeFhirData(patientResource, conditions)

        except Exception as e:
            logger.error(f"FHIR fetch failed: {e}")
            raise

    def _normalizeFhirData(self, patientResource: dict, conditions: list) -> dict:
        """Normalize FHIR resources into our schema."""
        nameData = patientResource.get("name", [{}])[0]
        return {
            "patientName": f"{nameData.get('given', [''])[0]} {nameData.get('family', '')}",
            "dateOfBirth": patientResource.get("birthDate", ""),
            "healthCardNumber": self._extractIdentifier(patientResource, "health-card"),
            "address": self._extractAddress(patientResource),
            "phoneNumber": self._extractTelecom(patientResource, "phone"),
            "email": self._extractTelecom(patientResource, "email"),
            "diagnosis": conditions[0].get("resource", {}).get("code", {}).get("text", ""),
            "clinicalNotes": "",
            "medications": [],
            "allergies": [],
        }

    @staticmethod
    def _extractIdentifier(patient: dict, system: str) -> str:
        for identifier in patient.get("identifier", []):
            if system in identifier.get("system", "").lower():
                return identifier.get("value", "")
        return ""

    @staticmethod
    def _extractAddress(patient: dict) -> str:
        addresses = patient.get("address", [])
        if not addresses:
            return ""
        addr = addresses[0]
        lines = addr.get("line", [])
        return f"{', '.join(lines)}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('postalCode', '')}"

    @staticmethod
    def _extractTelecom(patient: dict, telecomType: str) -> str:
        for telecom in patient.get("telecom", []):
            if telecom.get("system") == telecomType:
                return telecom.get("value", "")
        return ""

    def _simulateEmrData(self, patientId: str) -> Dict:
        """Generate realistic simulated EMR data for prototype demo."""
        logger.info(f"Using simulated EMR data for patient {patientId}")
        return {
            "patientName": "Jane Doe",
            "dateOfBirth": "1962-04-15",
            "healthCardNumber": "1234 567 890",
            "phn": "987654321",
            "address": "145 King Street, Toronto, ON M5H 1J8",
            "postalCode": "M5H 1J8",
            "phoneNumber": "416-555-0199",
            "email": "jane.doe@example.com",
            "sin": "123-456-789",
            "diagnosis": "Severe osteoarthritis of bilateral knees with chronic pain limiting mobility",
            "diagnosisOnsetDate": "2021-06-01",
            "clinicalNotes": (
                "Patient has marked difficulty walking more than 50 meters without "
                "rest. Unable to climb stairs without significant pain. Requires "
                "assistance with bathing and dressing on bad days. Prescribed "
                "analgesics and anti-inflammatories with limited relief. "
                "Total knee replacement recommended but delayed due to surgical "
                "wait list (estimated 14 months)."
            ),
            "medications": ["Celecoxib 200mg BID", "Acetaminophen 1g QID"],
            "allergies": ["Penicillin"],
            "prognosis": "Prolonged — expected to last 12+ months",
            "treatmentPlan": {
                "requiresLifeSustainingTherapy": False,
                "therapyType": None,
                "therapyFrequencyPerWeek": None,
            },
        }
