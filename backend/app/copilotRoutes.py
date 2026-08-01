"""
Copilot API routes — SSE streaming chat + patient search.

Endpoints:
  POST /api/v1/copilot/chat    — Stream AI response (SSE)
  GET  /api/v1/copilot/patients — Search patients (for autocomplete)
"""

import json
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.auth import requireRole
from app.models import Patient, User
from app.patientMatcher import matchPatient
from app.clinicalCopilot import streamCopilotResponse, processCopilotQuery

logger = logging.getLogger(__name__)

copilotApi = Blueprint("copilotApi", __name__, url_prefix="/api/v1/copilot")


@copilotApi.route("/chat", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def copilotChat():
    """
    Stream a copilot response via Server-Sent Events.

    Body: {
        "query": "What medications is Jon Doe on?",
        "history": [
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"}
        ]
    }

    Returns: SSE stream with events:
      data: {"type": "patient_match", "data": {"patientId": 1, "patientName": "John Doe", ...}}
      data: {"type": "no_patient", "data": {"message": "..."}}
      data: {"type": "thinking", "data": {}}
      data: {"type": "chunk", "data": {"content": "..."}}
      data: {"type": "done", "data": {"fullResponse": "..."}}
      data: {"type": "error", "data": {"message": "..."}}
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    history = data.get("history", [])

    if not query:
        return jsonify({"status": "error", "message": "Query is required"}), 400

    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).first()

    # Build physician info for the copilot (doctor's own info — not patient PII)
    physicianInfo = {}
    if user:
        # Look up clinic directly since User has no 'clinic' relationship
        from app.models import Clinic
        clinic = Clinic.query.filter_by(id=user.clinicId).first() if user.clinicId else None
        physicianInfo = {
            "physicianName": f"Dr. {user.firstName} {user.lastName}",
            "physicianLicense": user.licenseNumber or "",
            "clinicName": clinic.name if clinic else "",
            "clinicAddress": clinic.address if clinic else "",
            "clinicPhone": clinic.phoneNumber if clinic else "",
        }

    logger.info(f"Copilot chat from user {userId}: {query[:100]}...")

    def generate():
        try:
            for event in streamCopilotResponse(query, str(userId), history, physicianInfo):
                yield event
        except Exception as e:
            logger.error(f"Copilot SSE error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@copilotApi.route("/patients", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def searchPatients():
    """
    Search patients by name (fuzzy matching).

    Query params: ?q=Jon+Doe&limit=5

    Returns: {
        "patients": [
            {"id": 1, "name": "John Doe", "dob": "1985-03-15", "score": 0.92, "matchType": "fuzzy_full"}
        ]
    }
    """
    q = request.args.get("q", "").strip()
    limit = min(request.args.get("limit", 5, type=int), 20)

    if len(q) < 2:
        return jsonify({"patients": []})

    patients = Patient.query.all()
    matches = matchPatient(q, patients, threshold=0.3)

    results = []
    for m in matches[:limit]:
        p = m["patient"]
        results.append({
            "id": p.id,
            "name": p.patientName,
            "dob": p.dateOfBirth,
            "diagnosis": (p.diagnosis or "")[:80] + "..." if p.diagnosis and len(p.diagnosis) > 80 else p.diagnosis,
            "score": m["score"],
            "matchType": m["matchType"],
        })

    return jsonify({"patients": results})


@copilotApi.route("/preview", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def copilotPreview():
    """
    Preview what the copilot would do (non-streaming).
    Returns patient match info without generating a response.

    Body: {"query": "..."}
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"status": "error", "message": "Query is required"}), 400

    userId = get_jwt_identity()
    result = processCopilotQuery(query, str(userId))

    return jsonify({"status": "success", **result})
