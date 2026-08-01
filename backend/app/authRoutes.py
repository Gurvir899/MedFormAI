"""
Auth API routes — register, login, refresh, profile.

Email/password authentication with JWT tokens.
Supports doctor and patient roles with role-specific registration fields.
"""

import re
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User, Clinic
from app.database import db
from app.auth import generateTokens, requireRole
from app.rateLimiter import rateLimitLogin, rateLimitRegister

logger = logging.getLogger(__name__)

authApi = Blueprint("authApi", __name__, url_prefix="/api/v1/auth")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@authApi.route("/register", methods=["POST"])
@rateLimitRegister
def register():
    """
    Register a new user (doctor or patient).

    Body: {
        "email": "dr.smith@clinic.ca",
        "password": "SecurePass123!",
        "role": "doctor",               # or "patient"
        "firstName": "Sarah",
        "lastName": "Smith",
        "licenseNumber": "CPSO-12345",  # doctors only
        "specialty": "Family Medicine", # doctors only
        "clinicName": "Toronto Family Health",       # doctors only
        "clinicAddress": "100 Yonge St, Toronto, ON M5B 2L9"
    }
    """
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "doctor")
    firstName = data.get("firstName", "").strip()
    lastName = data.get("lastName", "").strip()

    # Validation
    if not email or not EMAIL_REGEX.match(email):
        return jsonify({"status": "error", "message": "Valid email required"}), 400
    if len(password) < 8:
        return jsonify({"status": "error", "message": "Password must be 8+ characters"}), 400
    if role not in ("doctor", "patient"):
        return jsonify({"status": "error", "message": "Role must be 'doctor' or 'patient'"}), 400
    if not firstName or not lastName:
        return jsonify({"status": "error", "message": "First and last name required"}), 400

    # Check existing
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"status": "error", "message": "Email already registered"}), 409

    # Doctor-specific validation
    licenseNumber = None
    specialty = None
    clinicId = None

    if role == "doctor":
        licenseNumber = data.get("licenseNumber", "").strip()
        if not licenseNumber:
            return jsonify({"status": "error", "message": "License number required for doctors"}), 400

        specialty = data.get("specialty", "").strip() or None

        # Create or find clinic
        clinicName = data.get("clinicName", "").strip()
        if clinicName:
            clinic = Clinic.query.filter_by(name=clinicName).first()
            if not clinic:
                clinic = Clinic(
                    name=clinicName,
                    address=data.get("clinicAddress", ""),
                )
                db.session.add(clinic)
                db.session.flush()
            clinicId = clinic.id

    # Create user
    user = User(
        email=email,
        role=role,
        firstName=firstName,
        lastName=lastName,
        licenseNumber=licenseNumber,
        specialty=specialty,
        clinicId=clinicId,
        isActive=True,
    )
    user.setPassword(password)
    db.session.add(user)
    db.session.commit()

    logger.info(f"New user registered: {email} ({role})")

    tokens = generateTokens(user)
    return jsonify({
        "status": "success",
        "message": "Registration successful",
        "user": user.toDict(includePii=True),
        **tokens,
    }), 201


@authApi.route("/login", methods=["POST"])
@rateLimitLogin
def login():
    """
    Login with email + password. Returns JWT tokens.

    Body: { "email": "...", "password": "..." }
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.checkPassword(password):
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    if not user.isActive:
        return jsonify({"status": "error", "message": "Account deactivated"}), 403

    tokens = generateTokens(user)
    return jsonify({
        "status": "success",
        "user": user.toDict(includePii=True),
        **tokens,
    })


@authApi.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    identity = get_jwt_identity()
    user = User.query.filter_by(id=identity).first()
    if not user or not user.isActive:
        return jsonify({"status": "error", "message": "User not found or inactive"}), 401

    tokens = generateTokens(user)
    return jsonify({"status": "success", **tokens})


@authApi.route("/me", methods=["GET"])
@jwt_required()
def getProfile():
    """Get current user profile."""
    identity = get_jwt_identity()
    user = User.query.filter_by(id=identity).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    profile = user.toDict(includePii=True)
    if user.clinicId:
        clinic = Clinic.query.filter_by(id=user.clinicId).first()
        if clinic:
            profile["clinic"] = clinic.toDict()
    return jsonify({"status": "success", "user": profile})


@authApi.route("/me", methods=["PUT"])
@jwt_required()
def updateProfile():
    """Update current user profile."""
    identity = get_jwt_identity()
    user = User.query.filter_by(id=identity).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    data = request.get_json() or {}

    if "firstName" in data:
        user.firstName = data["firstName"].strip()
    if "lastName" in data:
        user.lastName = data["lastName"].strip()
    if user.role == "doctor":
        if "licenseNumber" in data:
            user.licenseNumber = data["licenseNumber"].strip()
        if "specialty" in data:
            user.specialty = data["specialty"].strip()
    if "password" in data and data["password"]:
        if len(data["password"]) < 8:
            return jsonify({"status": "error", "message": "Password must be 8+ characters"}), 400
        user.setPassword(data["password"])

    db.session.commit()
    return jsonify({"status": "success", "user": user.toDict(includePii=True)})
