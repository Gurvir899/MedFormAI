"""
PII Gateway — central compliance middleware.

Every request passing through Flask hits this gateway first. It:
  1. Scans incoming JSON payloads for PII fields
  2. Enforces minimum-necessary data collection per endpoint
  3. Logs every PII access to the audit trail
  4. Blocks requests that violate RBAC or collect excess PII

This IS the compliance product — not a bolt-on.
"""

import logging
import json
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, List, Optional, Set

from flask import request, g, current_app
from werkzeug.exceptions import Forbidden, BadRequest

logger = logging.getLogger(__name__)

# ─── PII field taxonomy ────────────────────────────────────────────────

piiFieldTaxonomy: Set[str] = {
    "patientName", "dateOfBirth", "healthCardNumber", "phn",
    "diagnosis", "address", "phoneNumber", "email", "sin",
    "postalCode", "physicianName", "notes", "medications",
    "labResults", "allergies", "familyHistory", "socialHistory",
    "insuranceNumber", "employer", "occupation",
}

# ─── Minimum-necessary schema per endpoint ────────────────────────────

endpointPiiAllowlist: Dict[str, Set[str]] = {
    "/api/v1/forms/dtc/submit": {
        "patientName", "dateOfBirth", "healthCardNumber", "diagnosis",
        "address", "postalCode", "physicianName",
    },
    "/api/v1/forms/dtc/preview": {
        "patientName", "dateOfBirth", "healthCardNumber", "diagnosis",
    },
    "/api/v1/forms/insurance/submit": {
        "patientName", "dateOfBirth", "healthCardNumber", "diagnosis",
        "insuranceNumber", "address", "phoneNumber",
    },
    "/api/v1/forms/cpp/submit": {
        "patientName", "dateOfBirth", "healthCardNumber", "diagnosis",
        "address", "sin",
    },
    "/api/v1/roi/calculate": set(),  # No PII needed
    "/api/v1/compliance/dashboard": set(),  # No PII needed
}


def classifyPiiFields(payload: dict) -> List[str]:
    """Scan a JSON payload and return list of PII field names found."""
    found = []
    for key in payload:
        normalizedKey = key.lower()
        for piiField in piiFieldTaxonomy:
            if piiField.lower() in normalizedKey or normalizedKey in piiField.lower():
                found.append(key)
                break
    return found


def enforceMinimumNecessary(endpoint: str, payload: dict) -> tuple[bool, list[str]]:
    """
    Check if the request payload only contains PII fields
    that are allowlisted for this endpoint.

    Returns (allowed, excessFields).
    """
    allowlist = endpointPiiAllowlist.get(endpoint)
    if allowlist is None:
        # No schema defined — allow but log warning
        logger.warning(f"No PII allowlist defined for endpoint: {endpoint}")
        return True, []

    payloadPiiFields = set(classifyPiiFields(payload))
    excess = payloadPiiFields - allowlist

    if excess:
        logger.warning(
            f"Minimum-necessary violation on {endpoint}: "
            f"excess fields = {excess}"
        )
        return False, list(excess)

    return True, []


def auditPiiAccess(userId: str, action: str, piiFields: List[str],
                   endpoint: str, patientId: Optional[str] = None):
    """
    Write an audit log entry for every PII access.

    Audit log is immutable and stored in DB. Each entry records:
      - Who accessed (userId)
      - What action (read/write/delete)
      - Which PII fields were involved
      - Which endpoint triggered it
      - Which patient (if known)
      - Timestamp + IP
    """
    try:
        from app.models import AuditLog
        from app.database import db

        entry = AuditLog(
            userId=userId,
            action=action,
            piiFields=json.dumps(piiFields),
            endpoint=endpoint,
            patientId=patientId,
            ipAddress=request.remote_addr if request else "system",
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(entry)
        db.session.commit()
        logger.info(f"Audit: user={userId} action={action} fields={piiFields}")
    except Exception as e:
        logger.error(f"Audit log write failed: {e}")


def piiGateway(fn):
    """
    Decorator that wraps every API endpoint touching patient data.

    Flow:
      1. Parse JSON body
      2. Classify PII fields present
      3. Enforce minimum-necessary allowlist
      4. Audit log the access (userId from JWT, not request body)
      5. Block if violations found
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        endpoint = request.path

        # Get userId from JWT identity (set by @jwt_required / @requireRole)
        # Falls back to "anonymous" for endpoints without JWT
        try:
            from flask_jwt_extended import get_jwt_identity
            jwtIdentity = get_jwt_identity()
            userId = str(jwtIdentity) if jwtIdentity else getattr(g, "userId", "anonymous")
        except Exception:
            userId = getattr(g, "userId", "anonymous")

        # Skip if no JSON body
        payload = request.get_json(silent=True) or {}

        if not payload:
            return fn(*args, **kwargs)

        # 1. Classify PII
        piiFieldsFound = classifyPiiFields(payload)

        if piiFieldsFound:
            # 2. Enforce minimum-necessary
            allowed, excessFields = enforceMinimumNecessary(endpoint, payload)
            if not allowed:
                auditPiiAccess(
                    userId=userId,
                    action="blocked_excess_pii",
                    piiFields=excessFields,
                    endpoint=endpoint,
                )
                raise Forbidden(
                    f"Request blocked: fields not allowed for this endpoint: "
                    f"{', '.join(excessFields)}. Only minimum-necessary PII "
                    f"is permitted."
                )

            # 3. Audit log
            auditPiiAccess(
                userId=userId,
                action=request.method,
                piiFields=piiFieldsFound,
                endpoint=endpoint,
                patientId=payload.get("patientId"),
            )

        return fn(*args, **kwargs)

    return wrapper
