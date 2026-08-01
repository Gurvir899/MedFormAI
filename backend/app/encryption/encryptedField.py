"""
Field-level encryption for PII columns using Fernet (AES-128-CBC + HMAC-SHA256).

Every PII field (name, DOB, PHN, diagnosis, etc.) is encrypted individually
before storage. This means:
  - DB dump alone reveals nothing
  - Compromised DB user sees ciphertext, not plaintext
  - Per-field access can be logged/audited
  - Selective decryption: only decrypt fields needed for current task
"""

import logging
from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, Text

logger = logging.getLogger(__name__)


class EncryptedField(TypeDecorator):
    """
    SQLAlchemy column type that transparently encrypts/decrypts values.

    Usage:
        patientName = db.Column(EncryptedField())  # ← encrypted at rest
        dateOfBirth = db.Column(EncryptedField())
        provincialHealthNumber = db.Column(EncryptedField())
    """

    impl = Text
    cacheOk = True

    def __init__(self, *args, **kwargs):
        self._fernet = None
        super().__init__(*args, **kwargs)

    def _getFernet(self):
        """Lazy-load Fernet instance from app config."""
        if self._fernet is None:
            from flask import current_app
            key = current_app.config["ENCRYPTION_KEY"]
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        return self._fernet

    def processBindParam(self, value, dialect):
        """Encrypt value before storing in DB."""
        if value is None:
            return None
        fernet = self._getFernet()
        encrypted = fernet.encrypt(value.encode("utf-8"))
        logger.debug("Encrypted PII field for storage")
        return encrypted.decode("utf-8")

    def processResultValue(self, value, dialect):
        """Decrypt value after reading from DB."""
        if value is None:
            return None
        fernet = self._getFernet()
        decrypted = fernet.decrypt(value.encode("utf-8"))
        logger.debug("Decrypted PII field from storage")
        return decrypted.decode("utf-8")
