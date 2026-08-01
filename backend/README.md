# MedFormAI — Privacy-First Medical Form Automation

## Problem
Canadian physicians lose **19.8M hours/year** to unnecessary administrative tasks (CMA/CFIB 2026 Report). The #1 barrier to AI adoption is medico-legal/privacy risk (49% of physicians).

## Solution
Multi-agent pipeline that auto-completes Canada's most burdensome medical forms (DTC, insurance, CPP) with a built-in PII compliance layer.

## Architecture

```
Next.js Frontend → Flask API → [PII Gateway] → Multi-Agent Pipeline
                                                      ↓
                                            Agent 1: Data Extractor (EMR/FHIR)
                                            Agent 2: Form Filler (LLM + schema mapping)
                                            Agent 3: PII Guardian (compliance scan)
                                                      ↓
                                            PostgreSQL (field-level encrypted)
```

## Quick Start

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Compliance

- **Field-level encryption** (AES-256 via Fernet) on all PII columns
- **PII Gateway middleware** — minimum-necessary enforcement on every request
- **LLM redaction layer** — PII tokenized before any external API call
- **Immutable audit trail** — every PII access logged (who/what/when)
- **30-day retention** — form drafts auto-purged
