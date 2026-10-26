<div align="center">

# ⚙️ TenderCheck Backend Service

### **Async FastAPI Core, Gemini 2.0 Flash Extraction & Deterministic Verification Engine**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20Asyncpg-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Pytest](https://img.shields.io/badge/Tests-Pytest%20AsyncIO-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org/)

</div>

---

## 📖 Overview

The TenderCheck backend is an asynchronous, high-throughput service designed for automated tender bid compliance checking. It pairs Google Gemini 2.0 Flash for semantic understanding with zero-hallucination deterministic Python rule engines for verification.

### Core Architecture Principles
1. **Advisory AI, Human Decision**: Gemini parses unstructured clauses and extracts evidence; Python strictly computes numeric and boolean compliance; Procurement officers confirm or override verdicts.
2. **Hybrid OCR Extraction**: Digital PDFs extract via `PyMuPDF` in milliseconds. Scanned/low-res photocopies fall back automatically to `Tesseract OCR`.
3. **Cross-Document Contradiction Detection**: Scans across multiple files (technical specs, balance sheets, ISO audits) to detect conflicting claims.

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── api/v1/                   # Endpoint routers
│   │   ├── tenders.py            # Tender PDF ingestion & clause extraction
│   │   ├── vendor_documents.py   # Vendor bid upload & tracking
│   │   ├── matching.py           # Verification & contradiction execution
│   │   └── reports.py            # Audit reports & officer confirmation
│   ├── llm/
│   │   ├── client.py             # Google GenAI client lifecycle
│   │   └── prompts.py            # Sector-tailored clause extraction prompts
│   ├── models/                   # SQLAlchemy 2.0 async models
│   │   ├── tender.py             # Tender document entity
│   │   ├── requirement.py        # Extracted clauses & operators
│   │   ├── vendor_document.py    # Vendor-submitted bids & certificates
│   │   ├── match.py              # Individual compliance verdicts
│   │   ├── contradiction.py      # Cross-document conflict logs
│   │   └── report.py             # Consolidated officer audit report
│   ├── schemas/                  # Pydantic v2 validation contracts
│   ├── sectors/                  # Declarative sector definitions (e.g. it_hardware.json)
│   ├── services/
│   │   ├── pdf_extractor.py          # PyMuPDF + Tesseract OCR hybrid pipeline
│   │   ├── requirement_parser.py     # Gemini clause normalization
│   │   ├── matching_engine.py        # Evidence vector matching
│   │   ├── verification_engine.py    # Sandboxed deterministic Python rule engine
│   │   ├── contradiction_service.py  # Multi-file conflict detection
│   │   └── report_service.py         # Report generation & PDF exporter
│   ├── config.py                 # Pydantic settings & environment manager
│   ├── database.py               # Asyncpg session factory
│   └── main.py                   # FastAPI application initialization
├── alembic/                      # Database migrations
├── tests/                        # Comprehensive test suite
├── pyproject.toml                # Project metadata & dependencies
└── Dockerfile
```

---

## 🚀 Setup & Execution

### 1. Environment Configuration

Copy the example environment file and set your credentials:

```bash
cp .env.example .env
```

```env
# Gemini API Key (Required for clause & evidence parsing)
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.0-flash

# Database (AsyncPG driver for application, Psycopg2 for Alembic)
DATABASE_URL=postgresql+asyncpg://tendercheck:tendercheck@localhost:5432/tendercheck

# OCR & File Limits
UPLOAD_DIR=uploads
SECTOR=it_hardware
OCR_THRESHOLD=50
LLM_CONTEXT_LIMIT=120000
```

### 2. Local Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\Activate.ps1

# Install in editable mode with test dependencies
pip install -e ".[test]"

# Run database migrations
alembic upgrade head

# Launch development server with HMR
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Testing Suite

Run all unit, integration, and rule tests:

```bash
# Run pytest with async support
pytest

# Run tests with verbose output and coverage
pytest -v --asyncio-mode=auto
```

---

## 📡 Key REST Endpoints

| Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/tenders/upload` | Ingest tender PDF & extract clauses with Gemini Flash |
| `GET` | `/api/v1/tenders/{id}/requirements` | Retrieve parsed requirements and criteria |
| `POST` | `/api/v1/vendor-docs/upload` | Ingest vendor bid packets & certificates |
| `POST` | `/api/v1/matching/run/{tender_id}/{vendor}` | Run deterministic evaluation & discrepancy scanner |
| `GET` | `/api/v1/reports/{tender_id}/{vendor}` | View full compliance matrix with page citations |
| `POST` | `/report/confirm` | Authenticated procurement officer signoff & approval |
