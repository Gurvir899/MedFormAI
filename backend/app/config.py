import os
from cryptography.fernet import Fernet


class Config:
    """Application configuration with PII protection defaults."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI", "sqlite:///medformai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

    # Expose camelCase aliases for internal code
    @property
    def secretKey(self):
        return self.SECRET_KEY

    @property
    def databaseUri(self):
        return self.SQLALCHEMY_DATABASE_URI

    @property
    def corsOrigins(self):
        return self.CORS_ORIGINS

    # Encryption — Fernet symmetric encryption (AES-128-CBC + HMAC)
    encryptionKey = os.environ.get("ENCRYPTION_KEY", Fernet.generate_key().decode())

    # LLM API
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    # Audit
    AUDIT_LOG_ENABLED = os.environ.get("AUDIT_LOG_ENABLED", "true").lower() == "true"

    # Retention — auto-purge form drafts after N days
    DRAFT_RETENTION_DAYS = int(os.environ.get("DRAFT_RETENTION_DAYS", "30"))

    # PII Gateway
    PII_REDACT_BEFORE_LLM = True
    PII_LOG_ACCESS = True
    PII_MINIMUM_NECESSARY = True

    # camelCase aliases
    @property
    def llmApiKey(self): return self.LLM_API_KEY
    @property
    def llmBaseUrl(self): return self.LLM_BASE_URL
    @property
    def llmModel(self): return self.LLM_MODEL
    @property
    def auditLogEnabled(self): return self.AUDIT_LOG_ENABLED
    @property
    def draftRetentionDays(self): return self.DRAFT_RETENTION_DAYS
    @property
    def encryptionKey(self): return self.ENCRYPTION_KEY
    @property
    def piiRedactBeforeLlm(self): return self.PII_REDACT_BEFORE_LLM
    @property
    def piiLogAccess(self): return self.PII_LOG_ACCESS
    @property
    def piiMinimumNecessary(self): return self.PII_MINIMUM_NECESSARY
