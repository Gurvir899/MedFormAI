#!/usr/bin/env python3
"""
Paean Database Migration Script

Ensures all tables (existing + new) are created alongside existing data.
SQLite's CREATE TABLE IF NOT EXISTS means new tables are added without
touching existing data.

Run: python3 migrate.py
"""

import sys
import os

# Add backend dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import createApp
from app.database import db

def migrate():
    print("=== Paean Database Migration ===")

    app = createApp()

    with app.app_context():
        # Create all tables (IF NOT EXISTS — safe for existing DB)
        db.create_all()

        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        print(f"\nTables in database ({len(tables)}):")
        for t in sorted(tables):
            print(f"  ✓ {t}")

        # Count rows in each table
        from app.models import Patient, FormSubmission, AuditLog, User, Clinic

        print("\nRow counts:")
        for model, label in [
            (Patient, "patients"),
            (FormSubmission, "formSubmissions"),
            (AuditLog, "auditLogs"),
            (User, "users"),
            (Clinic, "clinics"),
        ]:
            try:
                count = db.session.query(model).count()
                print(f"  {label}: {count} rows")
            except Exception as e:
                print(f"  {label}: error — {e}")

    print("\n=== Migration Complete ===")


if __name__ == "__main__":
    migrate()
