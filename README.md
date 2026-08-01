# MedFormAI

Privacy-first medical form automation for Canadian physicians, built around a Gemma-powered multi-agent pipeline. Built for the **Clinical Triage** track (see [TRACKS.md](TRACKS.md)).

## Problem

Canadian physicians lose **19.8M hours/year** to unnecessary administrative work (CMA/CFIB 2026 report). The #1 barrier to AI adoption in clinical settings is medico-legal/privacy risk — cited by 49% of physicians.

## Solution

A multi-agent pipeline that auto-completes Canada's most burdensome medical forms — Disability Tax Credit (T2201), insurance, and CPP disability — from pasted clinical notes or EMR/FHIR data, with a compliance layer built in from the start rather than bolted on.

```
Next.js Frontend → Flask API → PII Gateway → Multi-Agent Pipeline
                                                     │
                                    Agent 1: Data Extractor (EMR/FHIR)
                                    Agent 2: Form Filler (LLM + schema mapping)
                                    Agent 3: PII Guardian (compliance scan)
                                                     │
                                    SQLite/PostgreSQL (field-level encrypted)
```

## How it works

1. **Data Extractor** pulls patient data from a FHIR R4 endpoint (if configured) or simulated EMR data.
2. **PII redaction layer** tokenizes direct identifiers (name, DOB, SIN, phone, email, health card, address) before anything reaches the LLM, and restores them afterward.
3. **Form Filler** maps extracted/redacted data onto the target form schema, using the LLM only for classification and narrative fields.
4. **PII Guardian** runs a final compliance pass — checks for excess fields, leaked identifiers in narrative text, and missing required fields — and produces a pass/fail compliance score before anything is stored.
5. Every PII-touching request goes through a **PII Gateway** that enforces a per-endpoint minimum-necessary allowlist and writes an immutable audit log entry.
6. PII columns are encrypted at rest (Fernet/AES) via a custom SQLAlchemy field type.

## Tech stack

- **Backend**: Flask 3, SQLAlchemy, JWT auth, Fernet field-level encryption, OpenAI-compatible LLM client (Gemma model)
- **Frontend**: Next.js 15, React 19, TypeScript
- **DB**: SQLite by default, swappable for PostgreSQL

## Project structure

```
backend/
  app/            Flask app factory, routes, auth, PII gateway, encryption
  agents/         Data Extractor, Form Filler, PII Guardian, pipeline orchestration
  schemas/        Form field schemas (DTC/T2201, sick note)
frontend/
  src/app/        Next.js pages (dashboard, forms, copilot, compliance, ROI, patients, appointments)
  src/components/ UI components
  src/lib/        API client, auth context, shared types
```

## Getting started

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py          # http://localhost:5000

# optional: seed demo data
python migrate.py
python seedData.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev             # http://localhost:8877
```

### Environment variables (backend)

Set these via a `.env` file in `backend/` (not committed — see `.gitignore`):

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev fallback | Flask/JWT signing secret — set a real value in production |
| `DATABASE_URI` | `sqlite:///medformai.db` | SQLAlchemy DB URI |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins — set to `http://localhost:8877` for local dev |
| `ENCRYPTION_KEY` | generated at boot if unset | Fernet key for encrypted PII columns — **must be set and persisted in production**, or previously encrypted data becomes unreadable after restart |
| `HERMES_CUSTOM_AI_SPURIC_COM_API_KEY` | none | API key for the LLM backend — required for LLM-powered features |
| `LLM_BASE_URL` | `https://ai.spuric.com/v1/` | OpenAI-compatible LLM endpoint |
| `LLM_MODEL` | `spur-gemma4` | LLM model name |
| `AUDIT_LOG_ENABLED` | `true` | Toggle PII audit logging |
| `DRAFT_RETENTION_DAYS` | `30` | Form draft retention policy |

### Docker

```bash
docker build -t medformai-backend ./backend
docker run -p 5000:5000 --env-file backend/.env medformai-backend

docker build -t medformai-frontend ./frontend
docker run -p 8877:8877 medformai-frontend
```

## Compliance features

- Field-level encryption (Fernet/AES) on all PII database columns
- PII Gateway middleware enforcing minimum-necessary data per endpoint
- LLM redaction layer — PII tokenized before any external API call, restored after
- Immutable audit trail of every PII access (who/what/when/endpoint)
- 30-day retention policy on form drafts

## License

MIT — see [LICENSE](LICENSE).
