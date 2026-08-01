"""
Authentication service — JWT token management + role-based access control.

Integrates with flask-jwt-extended for token creation/verification.
Provides requireRole decorator for RBAC on top of JWT auth.
"""

import logging
from datetime import timedelta
from functools import wraps
from typing import Optional

from flask import request, jsonify, g
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt_identity, verify_jwt_in_request,
)

from app.models import User

logger = logging.getLogger(__name__)

jwt = JWTManager()

# Token expiry
ACCESS_TOKEN_EXPIRY = timedelta(hours=24)
REFRESH_TOKEN_EXPIRY = timedelta(days=30)


def initJwt(app):
    """Initialize JWT manager on Flask app."""
    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_TOKEN_EXPIRY
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = REFRESH_TOKEN_EXPIRY
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"
    jwt.init_app(app)

    @jwt.user_lookup_loader
    def userLookupCallback(_jwtHeader, jwtData):
        identity = jwtData["sub"]
        return User.query.filter_by(id=identity).first()

    @jwt.expired_token_loader
    def expiredTokenCallback(jwtHeader, jwtPayload):
        return jsonify({"status": "error", "message": "Token expired"}), 401

    @jwt.invalid_token_loader
    def invalidTokenCallback(error):
        return jsonify({"status": "error", "message": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missingTokenCallback(error):
        return jsonify({"status": "error", "message": "Authorization required"}), 401


def requireRole(*roles):
    """
    Decorator: require the authenticated user to have one of the specified roles.
    Must be used after @jwt_required().
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            if identity is None:
                return jsonify({"status": "error", "message": "Not authenticated"}), 401
            user = User.query.filter_by(id=identity).first()
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 401
            if user.role not in roles:
                return jsonify({
                    "status": "error",
                    "message": f"Requires role: {', '.join(roles)}"
                }), 403
            g.userId = str(user.id)
            g.userRole = user.role
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def getJwtUser() -> Optional[User]:
    """Get the current authenticated user, or None."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity is None:
            return None
        return User.query.filter_by(id=identity).first()
    except Exception:
        return None


def generateTokens(user: User) -> dict:
    """Generate access + refresh tokens for a user."""
    accessToken = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email}
    )
    refreshToken = create_refresh_token(identity=str(user.id))
    return {
        "accessToken": accessToken,
        "refreshToken": refreshToken,
        "expiresIn": int(ACCESS_TOKEN_EXPIRY.total_seconds()),
    }
