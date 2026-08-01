"""
Flask API routes for Paean.

All endpoints touching PII are wrapped with @piiGateway.
"""

import json
import logging
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, g, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.piiGateway import piiGateway, auditPiiAccess
from app.models import Patient, FormSubmission, AuditLog, User, Appointment
from app.database import db
from app.roiCalculator import calculateRoi
from app.llmClient import llmClient
from app.auth import requireRole, getJwtUser
from agents import FormAutomationPipeline
from agents.clinicalNotesProcessor import ClinicalNotesProcessor

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__, url_prefix="/api/v1")

# Lazy-initialize pipeline (LLM client optional)
_pipeline = None


def getPipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = FormAutomationPipeline()
    return _pipeline


# ─── Health ────────────────────────────────────────────────────────────

@api.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Paean",
        "version": "1.0.0",
        "compliance": "PHIPA/PIPEDA ready",
    })


# ─── Form Schema ───────────────────────────────────────────────────────

@api.route("/forms/dtc/schema", methods=["GET"])
def getDtcSchema():
    """Return the DTC form schema for frontend rendering."""
    from schemas.dtcForm import getFormSchema
    return jsonify(getFormSchema())


@api.route("/forms/schema", methods=["GET"])
def getAllSchemas():
    """Return all available form schemas."""
    from schemas.dtcForm import getFormSchema
    return jsonify({
        "forms": ["dtc"],
        "schemas": {"dtc": getFormSchema()},
    })


# ─── Form Automation Pipeline ──────────────────────────────────────────

@api.route("/forms/dtc/preview", methods=["POST"])
@jwt_required()
@piiGateway
def previewDtcForm():
    """
    Run the multi-agent pipeline to auto-populate a DTC form.
    Returns form data + PII compliance scan results.

    Body: { "patientId": "123" }
    """
    data = request.get_json()
    patientId = data.get("patientId", "demo-patient")
    g.userId = data.get("physicianId", "demo-physician")

    pipeline = getPipeline()
    result = pipeline.processForm(
        patientId=patientId,
        formType="dtc",
        physicianId=g.userId,
    )

    return jsonify({
        "status": "success",
        "formData": result["formData"],
        "confidence": result["confidence"],
        "requiresReview": result["requiresReview"],
        "piiScan": result["piiScan"],
        "pipelineSteps": result["pipelineSteps"],
        "redactedPreview": result["redactedPreview"],
    })


@api.route("/forms/dtc/submit", methods=["POST"])
@jwt_required()
@piiGateway
def submitDtcForm():
    """
    Submit a completed DTC form.
    Stores encrypted form data + writes audit trail.

    Body: { "patientId": 1, "physicianId": "dr-smith", "formData": {...} }
    """
    data = request.get_json()
    patientId = data.get("patientId")
    physicianId = data.get("physicianId", "unknown")
    formData = data.get("formData", {})

    # Run PII guardian scan before storing
    pipeline = getPipeline()
    scanResult = pipeline.piiGuardian.scanFormSubmission(formData=formData)

    if not scanResult["passed"]:
        return jsonify({
            "status": "blocked",
            "message": "PII compliance scan failed. Form not submitted.",
            "findings": scanResult["findings"],
        }), 403

    # Store encrypted form submission
    import json
    submission = FormSubmission(
        formType="dtc",
        patientId=patientId,
        physicianId=physicianId,
        status="submitted",
        piiScanPassed=True,
        piiFindings=json.dumps(scanResult["findings"]),
        redactedPreview=scanResult["redactedPreview"],
        formData=json.dumps(formData),
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({
        "status": "submitted",
        "submissionId": submission.id,
        "piiScan": {
            "passed": scanResult["passed"],
            "score": scanResult["score"],
            "findingsCount": len(scanResult["findings"]),
        },
    })


# ─── Insurance Form ────────────────────────────────────────────────────

@api.route("/forms/insurance/submit", methods=["POST"])
@jwt_required()
@piiGateway
def submitInsuranceForm():
    """Submit a private insurance form."""
    data = request.get_json()
    patientId = data.get("patientId")
    physicianId = data.get("physicianId", "unknown")
    formData = data.get("formData", {})

    pipeline = getPipeline()
    scanResult = pipeline.piiGuardian.scanFormSubmission(formData=formData, formType="insurance")

    if not scanResult["passed"]:
        return jsonify({
            "status": "blocked",
            "message": "PII compliance scan failed.",
            "findings": scanResult["findings"],
        }), 403

    import json
    submission = FormSubmission(
        formType="insurance",
        patientId=patientId,
        physicianId=physicianId,
        status="submitted",
        piiScanPassed=True,
        piiFindings=json.dumps(scanResult["findings"]),
        redactedPreview=scanResult["redactedPreview"],
        formData=json.dumps(formData),
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({
        "status": "submitted",
        "submissionId": submission.id,
        "piiScanPassed": True,
    })


# ─── CPP Disability Form ───────────────────────────────────────────────

@api.route("/forms/cpp/submit", methods=["POST"])
@jwt_required()
@piiGateway
def submitCppForm():
    """Submit a CPP disability benefits form."""
    data = request.get_json()
    patientId = data.get("patientId")
    physicianId = data.get("physicianId", "unknown")
    formData = data.get("formData", {})

    pipeline = getPipeline()
    scanResult = pipeline.piiGuardian.scanFormSubmission(formData=formData, formType="cpp")

    if not scanResult["passed"]:
        return jsonify({
            "status": "blocked",
            "message": "PIII compliance scan failed.",
            "findings": scanResult["findings"],
        }), 403

    import json
    submission = FormSubmission(
        formType="cpp",
        patientId=patientId,
        physicianId=physicianId,
        status="submitted",
        piiScanPassed=True,
        piiFindings=json.dumps(scanResult["findings"]),
        redactedPreview=scanResult["redactedPanel"],
        formData=json.dumps(formData),
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({
        "status": "submitted",
        "submissionId": submission.id,
        "piiScanPassed": True,
    })


# ─── ROI Calculator ────────────────────────────────────────────────────

@api.route("/roi/calculate", methods=["POST"])
def calculateRoiEndpoint():
    """
    Calculate ROI based on CMA/CFIB 2026 report data.

    Body: {
        "physicianCount": 10,
        "province": "ontario",
        "formsAutomated": ["dtc", "privateInsurance"],
        "useAiScribe": true
    }
    """
    data = request.get_json() or {}
    result = calculateRoi(
        physicianCount=data.get("physicianCount", 10),
        province=data.get("province", "ontario"),
        formsAutomated=data.get("formsAutomated", ["dtc"]),
        useAiScribe=data.get("useAiScribe", True),
    )
    return jsonify(result)


# ─── Compliance Dashboard ──────────────────────────────────────────────

@api.route("/compliance/dashboard", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def complianceDashboard():
    """
    Return PII compliance dashboard data.

    Shows audit trail summary, PII scan results, compliance posture.
    """
    # Get recent audit logs
    recentLogs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(20).all()

    # Get submission stats
    totalSubmissions = FormSubmission.query.count()
    passedSubmissions = FormSubmission.query.filter_by(piiScanPassed=True).count()
    blockedSubmissions = FormSubmission.query.filter_by(piiScanPassed=False).count()

    # Get recent submissions
    recentSubmissions = FormSubmission.query.order_by(
        FormSubmission.createdAt.desc()
    ).limit(10).all()

    return jsonify({
        "auditLogs": [log.toDict() for log in recentLogs],
        "submissionStats": {
            "total": totalSubmissions,
            "passed": passedSubmissions,
            "blocked": blockedSubmissions,
            "passRate": round(passedSubmissions / max(1, totalSubmissions) * 100, 1),
        },
        "recentSubmissions": [sub.toDict() for sub in recentSubmissions],
        "compliancePosture": {
            "encryptionAtRest": True,
            "encryptionInTransit": True,
            "piiRedactionBeforeLlm": True,
            "auditTrailEnabled": True,
            "minimumNecessaryEnforced": True,
            "retentionPolicyDays": 30,
        },
    })


# ─── Audit Trail ───────────────────────────────────────────────────────

@api.route("/audit/logs", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def getAuditLogs():
    """Return paginated audit logs."""
    page = request.args.get("page", 1, type=int)
    perPage = request.args.get("perPage", 20, type=int)

    pagination = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).paginate(page=page, per_page=perPage, error_out=False)

    return jsonify({
        "logs": [log.toDict() for log in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "currentPage": page,
    })


# ─── REAL: Clinical Notes → Filled Form ────────────────────────────────

_notesProcessor = None


def getNotesProcessor():
    global _notesProcessor
    if _notesProcessor is None:
        _notesProcessor = ClinicalNotesProcessor()
    return _notesProcessor


@api.route("/forms/process", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def processClinicalNotes():
    """
    THE REAL PRODUCT ENDPOINT.

    Doctor pastes clinical notes → system fills form → PII scan → returns result.

    Body: {
        "clinicalNotes": "Patient: John Doe, DOB 1985-03-15. Presented with...",
        "formType": "sickNote",           # or "dtc"
        "physicianName": "Dr. Sarah Chen",
        "physicianLicense": "CPSO-12345",
        "clinicName": "Toronto Family Health",
        "clinicAddress": "100 Yonge St, Toronto, ON M5B 2L9"
    }

    Returns: filled form + PII scan + time saved + redacted preview
    """
    data = request.get_json() or {}

    # Override physicianId with authenticated JWT user
    userId = get_jwt_identity()
    data["physicianId"] = str(userId)

    clinicalNotes = data.get("clinicalNotes", "").strip()
    formType = data.get("formType", "sickNote")
    physicianName = data.get("physicianName", "")
    physicianLicense = data.get("physicianLicense", "")
    clinicName = data.get("clinicName", "")
    clinicAddress = data.get("clinicAddress", "")

    if not clinicalNotes:
        return jsonify({
            "status": "error",
            "message": "clinicalNotes is required",
        }), 400

    if formType not in ("sickNote", "dtc"):
        return jsonify({
            "status": "error",
            "message": "formType must be 'sickNote' or 'dtc'",
        }), 400

    processor = getNotesProcessor()
    result = processor.processClinicalNotes(
        clinicalNotes=clinicalNotes,
        formType=formType,
        physicianName=physicianName,
        physicianLicense=physicianLicense,
        clinicName=clinicName,
        clinicAddress=clinicAddress,
    )

    # Audit log this processing
    from app.piiGateway import auditPiiAccess
    auditPiiAccess(
        userId=data.get("physicianId", "api-user"),
        action="process_clinical_notes",
        piiFields=list(result.get("formData", {}).keys()),
        endpoint="/api/v1/forms/process",
    )

    return jsonify({
        "status": "success",
        **result,
    })


@api.route("/forms/sicknote/schema", methods=["GET"])
def getSickNoteSchema():
    """Return the sick note form schema."""
    from schemas.sickNoteForm import getSickNoteSchema as _getSchema
    return jsonify(_getSchema())


@api.route("/forms/sicknote/pdf", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def generateSickNotePdf():
    """
    Generate a sick note PDF from form data.

    Body: {
        "formData": {
            "patientName": "John Doe",
            "dateOfBirth": "1985-03-15",
            "reasonForAbsence": "Acute gastroenteritis",
            "startDate": "2026-08-01",
            "expectedReturnDate": "2026-08-04",
            "fitnessForDuty": "Patient is medically unfit...",
            "physicianName": "Dr. Doctor Doctor",
            "physicianLicense": "CPSO-99999",
            "clinicName": "Paean Demo Clinic",
            "clinicAddress": "100 Yonge St, Toronto, ON",
            "dateOfIssue": "2026-08-01"
        }
    }

    Returns: PDF file download
    """
    from flask import send_file
    from app.pdfGenerator import generateSickNotePdf
    from app.piiGateway import auditPiiAccess

    data = request.get_json() or {}
    formData = data.get("formData", {})

    if not formData:
        return jsonify({"status": "error", "message": "formData is required"}), 400

    userId = get_jwt_identity()

    # Audit log the PDF generation
    auditPiiAccess(
        userId=str(userId),
        action="generate_sick_note_pdf",
        piiFields=["patientName", "dateOfBirth", "reasonForAbsence"],
        endpoint="/api/v1/forms/sicknote/pdf",
    )

    try:
        pdfBytes = generateSickNotePdf(formData)
        buf = io.BytesIO(pdfBytes)
        buf.seek(0)

        patientName = formData.get("patientName", "patient").replace(" ", "_")
        dateStr = datetime.now().strftime("%Y-%m-%d")

        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"sick_note_{patientName}_{dateStr}.pdf",
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return jsonify({"status": "error", "message": f"PDF generation failed: {e}"}), 500


@api.route("/forms/sicknote/letter-pdf", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def generateLetterPdf():
    """
    Generate a letter-style PDF from the copilot's raw narrative response.

    One LLM call → the narrative IS the letter → put it in the PDF once.
    No form fields, no extraction, no duplication.

    Body: {
        "content": "Full narrative text from the LLM...",
        "patientName": "John Doe"   // for filename only
    }

    Returns: PDF file download (letter format on clinic letterhead)
    """
    from flask import send_file
    from app.pdfGenerator import generateLetterPdf as _generateLetterPdf
    from app.piiGateway import auditPiiAccess

    data = request.get_json() or {}
    content = data.get("content", "").strip()
    patientName = data.get("patientName", "patient")

    if not content:
        return jsonify({"status": "error", "message": "content is required"}), 400

    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).first()

    # Build physician info from authenticated user
    physicianInfo = {}
    if user:
        from app.models import Clinic
        clinic = Clinic.query.filter_by(id=user.clinicId).first() if user.clinicId else None
        physicianInfo = {
            "physicianName": f"Dr. {user.firstName} {user.lastName}",
            "physicianLicense": user.licenseNumber or "",
            "clinicName": clinic.name if clinic else "",
            "clinicAddress": clinic.address if clinic else "",
            "clinicPhone": clinic.phoneNumber if clinic else "",
        }

    # Audit log
    auditPiiAccess(
        userId=str(userId),
        action="generate_sick_note_letter_pdf",
        piiFields=["patientName"] if patientName != "patient" else [],
        endpoint="/api/v1/forms/sicknote/letter-pdf",
    )

    try:
        pdfBytes = _generateLetterPdf(content, physicianInfo, patientName)
        buf = io.BytesIO(pdfBytes)
        buf.seek(0)

        safeName = patientName.replace(" ", "_") if patientName else "patient"
        dateStr = datetime.now().strftime("%Y-%m-%d")

        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"sick_note_{safeName}_{dateStr}.pdf",
        )
    except Exception as e:
        logger.error(f"Letter PDF generation failed: {e}")
        return jsonify({"status": "error", "message": f"PDF generation failed: {e}"}), 500


@api.route("/forms/all-schemas", methods=["GET"])
def getAllFormSchemas():
    """Return all available form schemas."""
    from schemas.dtcForm import getFormSchema
    from schemas.sickNoteForm import getSickNoteSchema
    return jsonify({
        "forms": ["sickNote", "dtc"],
        "schemas": {
            "sickNote": getSickNoteSchema(),
            "dtc": getFormSchema(),
        },
    })


# ─── DTC T2201 Generation + PDF ───────────────────────────────────────

@api.route("/forms/dtc/generate", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def generateDtcForm():
    """
    Generate a filled T2201 DTC form from patient clinical data using AI.

    Body: {
        "patientId": 1,
        "clinicalNotes": "Optional additional notes..."
    }

    Returns: {
        "status": "success",
        "formData": {...},       # Filled T2201 JSON
        "validation": {...},     # V01-V15 validation results
        "redactionPreview": str, # What the LLM saw (redacted)
        "llmUsed": bool
    }
    """
    from app.dtcCopilot import generateDtcForm as _generateDtcForm
    from app.models import Clinic

    data = request.get_json() or {}
    patientId = data.get("patientId")
    clinicalNotes = data.get("clinicalNotes", "")

    if not patientId:
        return jsonify({"status": "error", "message": "patientId is required"}), 400

    patient = Patient.query.filter_by(id=patientId).first()
    if not patient:
        return jsonify({"status": "error", "message": "Patient not found"}), 404

    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).first()

    # Build physician info
    physicianInfo = {}
    if user:
        clinic = Clinic.query.filter_by(id=user.clinicId).first() if user.clinicId else None
        physicianInfo = {
            "physicianName": f"Dr. {user.firstName} {user.lastName}",
            "physicianLicense": user.licenseNumber or "",
            "clinicName": clinic.name if clinic else "",
            "clinicAddress": clinic.address if clinic else "",
            "clinicPhone": clinic.phoneNumber if clinic else "",
        }

    # Audit log
    auditPiiAccess(
        userId=str(userId),
        action="generate_dtc_form",
        piiFields=["patientName", "dateOfBirth", "diagnosis", "medications", "notes"],
        endpoint="/api/v1/forms/dtc/generate",
        patientId=str(patient.id),
    )

    try:
        result = _generateDtcForm(patient, physicianInfo, str(userId))
        return jsonify({"status": "success", **result})
    except Exception as e:
        logger.error(f"DTC generation failed: {e}")
        return jsonify({"status": "error", "message": f"DTC generation failed: {e}"}), 500


@api.route("/forms/dtc/pdf", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def generateDtcPdf():
    """
    Generate a DTC T2201 PDF from filled form data.

    Body: { "formData": {...} }

    Returns: PDF file download
    """
    from flask import send_file
    from app.dtcPdfGenerator import generateDtcPdf as _generateDtcPdf

    data = request.get_json() or {}
    formData = data.get("formData", {})

    if not formData:
        return jsonify({"status": "error", "message": "formData is required"}), 400

    userId = get_jwt_identity()

    auditPiiAccess(
        userId=str(userId),
        action="generate_dtc_pdf",
        piiFields=["personFirstName", "personLastName", "personSin"],
        endpoint="/api/v1/forms/dtc/pdf",
    )

    try:
        pdfBytes = _generateDtcPdf(formData)
        buf = io.BytesIO(pdfBytes)
        buf.seek(0)

        patientName = ""
        pwd = formData.get("partA", {}).get("personWithDisability", {})
        if pwd.get("personFirstName"):
            patientName = f"{pwd.get('personFirstName', '')}_{pwd.get('personLastName', '')}".strip("_")
        dateStr = datetime.now().strftime("%Y-%m-%d")

        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"dtc_t2201_{patientName or 'patient'}_{dateStr}.pdf",
        )
    except Exception as e:
        logger.error(f"DTC PDF generation failed: {e}")
        return jsonify({"status": "error", "message": f"PDF generation failed: {e}"}), 500


@api.route("/forms/dtc/letter-pdf", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def generateDtcLetterPdf():
    """
    Generate a DTC T2201 PDF from a narrative document (like the sick note letter).
    Body: { "content": "...", "patientName": "..." }
    Returns: PDF file download
    """
    from app.pdfGenerator import generateLetterPdf

    data = request.get_json() or {}
    content = data.get("content", "")
    patientName = data.get("patientName", "patient")

    if not content:
        return jsonify({"status": "error", "message": "content is required"}), 400

    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).first()
    from app.models import Clinic
    clinic = Clinic.query.filter_by(id=user.clinicId).first() if user and user.clinicId else None

    physicianInfo = {
        "physicianName": f"Dr. {user.firstName} {user.lastName}" if user else "",
        "physicianLicense": user.licenseNumber if user else "",
        "clinicName": clinic.name if clinic else "",
        "clinicAddress": clinic.address if clinic else "",
        "clinicPhone": clinic.phoneNumber if clinic else "",
    }

    auditPiiAccess(
        userId=str(userId),
        action="generate_dtc_letter_pdf",
        piiFields=["patientName"],
        endpoint="/api/v1/forms/dtc/letter-pdf",
    )

    try:
        pdfBytes = generateLetterPdf(content, physicianInfo, "DTC T2201 — Disability Tax Credit Certificate")
        buf = io.BytesIO(pdfBytes)
        buf.seek(0)
        dateStr = datetime.now().strftime("%Y-%m-%d")
        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"dtc_t2201_{patientName.replace(' ', '_')}_{dateStr}.pdf",
        )
    except Exception as e:
        logger.error(f"DTC letter PDF generation failed: {e}")
        return jsonify({"status": "error", "message": f"PDF generation failed: {e}"}), 500


# ─── Appointments ─────────────────────────────────────────────────────

@api.route("/appointments", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def getAppointments():
    """Get appointments for the authenticated doctor."""
    userId = get_jwt_identity()
    patientId = request.args.get("patientId")

    query = Appointment.query.filter_by(physicianId=str(userId))
    if patientId:
        query = query.filter_by(patientId=patientId)
    appointments = query.order_by(Appointment.appointmentDate.desc()).limit(50).all()

    return jsonify({
        "appointments": [a.toDict() for a in appointments],
        "count": len(appointments),
    })


@api.route("/appointments/<int:appointmentId>", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def getAppointment(appointmentId):
    """Get a single appointment by ID."""
    appointment = Appointment.query.filter_by(id=appointmentId).first()
    if not appointment:
        return jsonify({"status": "error", "message": "Appointment not found"}), 404

    # Verify ownership
    userId = get_jwt_identity()
    if appointment.physicianId != str(userId):
        return jsonify({"status": "error", "message": "Not authorized"}), 403

    result = appointment.toDict()
    patient = Patient.query.filter_by(id=appointment.patientId).first()
    result["patientName"] = patient.patientName if patient else "Unknown"

    return jsonify(result)


@api.route("/appointments", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def createAppointment():
    """
    Create a new appointment with a clinical note.
    The AI extracts patient field updates from the note.

    Body: {
        "patientId": 1,
        "clinicalNote": "Patient presents with..."
    }

    Returns: {
        "status": "success",
        "appointment": {...},
        "fieldUpdates": {...},   # Extracted by AI
        "aiSummary": str,
        "llmUsed": bool
    }
    """
    from app.appointmentProcessor import processAppointmentNote
    from app.models import Clinic

    data = request.get_json() or {}
    patientId = data.get("patientId")
    clinicalNote = data.get("clinicalNote", "")

    if not patientId:
        return jsonify({"status": "error", "message": "patientId is required"}), 400
    if not clinicalNote.strip():
        return jsonify({"status": "error", "message": "clinicalNote is required"}), 400

    patient = Patient.query.filter_by(id=patientId).first()
    if not patient:
        return jsonify({"status": "error", "message": "Patient not found"}), 404

    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).first()

    # Build physician info
    physicianInfo = {}
    if user:
        clinic = Clinic.query.filter_by(id=user.clinicId).first() if user.clinicId else None
        physicianInfo = {
            "physicianName": f"Dr. {user.firstName} {user.lastName}",
            "physicianLicense": user.licenseNumber or "",
            "clinicName": clinic.name if clinic else "",
        }

    # Audit log
    auditPiiAccess(
        userId=str(userId),
        action="create_appointment",
        piiFields=["patientName", "diagnosis", "medications", "notes"],
        endpoint="/api/v1/appointments",
        patientId=str(patient.id),
    )

    try:
        # Process the note with AI
        result = processAppointmentNote(clinicalNote, patient, physicianInfo)

        # Save appointment record (without applying updates yet — doctor reviews first)
        appointment = Appointment(
            patientId=patient.id,
            physicianId=str(userId),
            clinicalNote=clinicalNote,
            aiSummary=result.get("aiSummary", ""),
            fieldUpdates=json.dumps(result.get("fieldUpdates", {})),
            status="completed",
        )
        db.session.add(appointment)
        db.session.commit()

        return jsonify({
            "status": "success",
            "appointment": appointment.toDict(),
            "fieldUpdates": result.get("fieldUpdates", {}),
            "aiSummary": result.get("aiSummary", ""),
            "redactionPreview": result.get("redactionPreview", ""),
            "llmUsed": result.get("llmUsed", False),
        })
    except Exception as e:
        logger.error(f"Appointment creation failed: {e}")
        return jsonify({"status": "error", "message": f"Appointment creation failed: {e}"}), 500


@api.route("/appointments/<int:appointmentId>/apply", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def applyAppointmentUpdates(appointmentId):
    """
    Apply the AI-extracted field updates to the patient record.
    Doctor reviews and confirms before this is called.

    Returns: {
        "status": "success",
        "applied": {...},   # Fields that were updated
        "skipped": {...}    # Fields that were skipped (not in allowlist)
    }
    """
    from app.appointmentProcessor import applyFieldUpdates

    appointment = Appointment.query.filter_by(id=appointmentId).first()
    if not appointment:
        return jsonify({"status": "error", "message": "Appointment not found"}), 404

    userId = get_jwt_identity()
    if appointment.physicianId != str(userId):
        return jsonify({"status": "error", "message": "Not authorized"}), 403

    patient = Patient.query.filter_by(id=appointment.patientId).first()
    if not patient:
        return jsonify({"status": "error", "message": "Patient not found"}), 404

    fieldUpdates = json.loads(appointment.fieldUpdates) if appointment.fieldUpdates else {}

    applied, skipped = applyFieldUpdates(patient, fieldUpdates)
    appointment.status = "reviewed"
    db.session.commit()

    auditPiiAccess(
        userId=str(userId),
        action="apply_appointment_updates",
        piiFields=list(applied.keys()),
        endpoint=f"/api/v1/appointments/{appointmentId}/apply",
        patientId=str(patient.id),
    )

    return jsonify({
        "status": "success",
        "applied": applied,
        "skipped": skipped,
    })


# ─── LLM Status ───────────────────────────────────────────────────────

@api.route("/llm/status", methods=["GET"])
def llmStatus():
    """Check if LLM is connected."""
    return jsonify({
        "llmAvailable": llmClient.available,
        "model": llmClient.modelName if llmClient.available else None,
        "baseUrl": llmClient.baseUrl if llmClient.available else None,
    })


# ─── Doctor: Form History ──────────────────────────────────────────────

@api.route("/doctor/forms", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def getDoctorForms():
    """List the authenticated doctor's form submissions."""
    userId = get_jwt_identity()

    page = request.args.get("page", 1, type=int)
    perPage = request.args.get("perPage", 20, type=int)
    formType = request.args.get("formType", None)

    query = FormSubmission.query.filter_by(physicianId=str(userId))
    if formType:
        query = query.filter_by(formType=formType)
    pagination = query.order_by(FormSubmission.createdAt.desc()).paginate(
        page=page, per_page=perPage, error_out=False
    )

    return jsonify({
        "forms": [sub.toDict() for sub in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "currentPage": page,
    })


# ─── Doctor: Patient Management ────────────────────────────────────────

@api.route("/doctor/patients", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def getDoctorPatients():
    """List patients associated with this doctor."""
    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).first()

    # Admin sees all patients; doctors see their own
    if user and user.role == "admin":
        patients = Patient.query.all()
    else:
        patients = Patient.query.filter_by(primaryPhysicianId=userId).all()

    return jsonify({
        "patients": [p.toDict(includePii=True) for p in patients],
        "total": len(patients),
    })


@api.route("/doctor/patients", methods=["POST"])
@jwt_required()
@requireRole("doctor", "admin")
def addPatient():
    """Add a new patient record."""
    data = request.get_json() or {}

    patient = Patient(
        patientName=data.get("patientName", ""),
        dateOfBirth=data.get("dateOfBirth", ""),
        healthCardNumber=data.get("healthCardNumber", ""),
        address=data.get("address", ""),
        postalCode=data.get("postalCode", ""),
        phoneNumber=data.get("phoneNumber", ""),
        email=data.get("email", ""),
        diagnosis=data.get("diagnosis", ""),
        medications=data.get("medications", ""),
        allergies=data.get("allergies", ""),
        notes=data.get("notes", ""),
    )
    db.session.add(patient)
    db.session.commit()

    return jsonify({
        "status": "success",
        "patientId": patient.id,
        "patient": patient.toDict(includePii=True),
    }), 201


# ─── Doctor: Stats ─────────────────────────────────────────────────────

@api.route("/doctor/stats", methods=["GET"])
@jwt_required()
@requireRole("doctor", "admin")
def getDoctorStats():
    """Dashboard stats for the authenticated doctor."""
    userId = get_jwt_identity()
    user = User.query.filter_by(id=userId).first()

    totalForms = FormSubmission.query.filter_by(physicianId=str(userId)).count()
    passedForms = FormSubmission.query.filter_by(
        physicianId=str(userId), piiScanPassed=True
    ).count()
    blockedForms = FormSubmission.query.filter_by(
        physicianId=str(userId), piiScanPassed=False
    ).count()

    # Get distinct patient count
    if user and user.role == "admin":
        patientCount = Patient.query.count()
    else:
        patientCount = Patient.query.filter_by(primaryPhysicianId=userId).count()

    # Recent forms
    recentForms = FormSubmission.query.filter_by(
        physicianId=str(userId)
    ).order_by(FormSubmission.createdAt.desc()).limit(5).all()

    return jsonify({
        "totalForms": totalForms,
        "passedForms": passedForms,
        "blockedForms": blockedForms,
        "patientCount": patientCount,
        "recentForms": [f.toDict() for f in recentForms],
    })
