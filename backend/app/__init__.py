"""
Paean — Flask Application Factory

Privacy-first medical form automation with built-in PII compliance.

Compliance: PHIPA (Ontario), PIPEDA (Federal), HIPAA-aligned
Architecture: Multi-agent pipeline + PII Gateway + Field-level encryption
"""

import logging
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.database import db


def createApp(configClass=Config) -> Flask:
    """Application factory with compliance defaults."""
    app = Flask(__name__)
    app.config.from_object(configClass)

    # Logging — structured, no PII in logs
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Suppress PII in logs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    # Database
    db.init_app(app)

    # JWT Auth
    from app.auth import initJwt
    initJwt(app)

    # CORS — restrict to known origins
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    # Register routes
    from app.routes import api as apiBlueprint
    app.register_blueprint(apiBlueprint)

    from app.authRoutes import authApi
    app.register_blueprint(authApi)

    from app.copilotRoutes import copilotApi
    app.register_blueprint(copilotApi)

    # Security headers
    @app.after_request
    def securityHeaders(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "img-src 'self' data:; "
            "object-src 'none'"
        )
        return response

    # Create tables
    with app.app_context():
        db.create_all()
        app.logger.info("Database initialized — all tables created")
        app.logger.info("Paean backend ready — PHIPA/PIPEDA compliance layer active")

    return app


# WSGI entry point
app = createApp()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
