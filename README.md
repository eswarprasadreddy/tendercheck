<div align="center">

# TenderCheck

**Automated compliance verification and cross-document discrepancy auditing for enterprise & public procurement tenders.**

[![CI](https://img.shields.io/github/actions/workflow/status/eswarprasadreddy/tendercheck/ci.yml?branch=main&style=flat-square&label=CI&color=18181b)](https://github.com/eswarprasadreddy/tendercheck/actions)
[![Release](https://img.shields.io/github/v/release/eswarprasadreddy/tendercheck?style=flat-square&color=18181b)](https://github.com/eswarprasadreddy/tendercheck/releases)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-3b82f6?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-059669?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.3-0284c7?style=flat-square)](https://react.dev)
[![License](https://img.shields.io/badge/license-MIT-71717a?style=flat-square)](LICENSE)

<p align="center">
  <a href="#overview">Overview</a> &bull;
  <a href="#how-it-works">How It Works</a> &bull;
  <a href="#core-features">Features</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#api-reference">API Reference</a> &bull;
  <a href="#sector-configuration">Sector Config</a>
</p>

</div>

---

## Overview

Public tenders (such as GeM in India or state procurement RFPs) span hundreds of pages of complex technical, financial, and legal criteria. Evaluating multiple vendor bids manually requires hours of cross-referencing PDFs, spreadsheets, and certificates—a process prone to human oversight, calculation mistakes, and undetected vendor discrepancies.

**TenderCheck** automates the end-to-end evaluation pipeline with a **human-in-the-loop, zero-hallucination verification model**:

- **Semantic Clause Normalization**: Extracts and parses dense tender clauses into typed, structured criteria using Gemini 2.0 Flash.
- **Deterministic Python Verification**: Eliminates LLM math and date errors. Numerical specifications (RAM, SSD, screen size), financial minimums (average turnover, net worth), and certificate expirations are computed by sandboxed Python logic.
- **Cross-Document Discrepancy Auditing**: Automatically flags conflicts across separate vendor uploads (e.g., claiming 32 GB RAM in the compliance summary while attaching an OEM datasheet specifying 16 GB).
- **Officer Audit Trail**: The platform is strictly advisory. Every determination includes page-level citations, side-by-side evidence inspection, and requires explicit procurement officer review and sign-off.

---

## How It Works

```
┌────────────────────────┐      ┌────────────────────────┐
│  Tender Document (PDF) │      │  Vendor Packets (PDFs) │
│  (GeM / RFP Clauses)   │      │  (Specs, P&L, Audits)  │
└───────────┬────────────┘      └───────────┬────────────┘
            │                               │
            ▼                               ▼
  PyMuPDF + Tesseract OCR        PyMuPDF + Tesseract OCR
            │                               │
            ▼                               │
  Gemini 2.0 Flash Parser                   │
  (Structured Clause Schema)                │
            │                               │
            ▼                               ▼
    ┌──────────────────────────────────────────────┐
    │          Deterministic Match Engine          │
    │  - Specification checks (e.g., RAM >= 16GB)  │
    │  - Financial thresholds (Turnover, Networth) │
    │  - Certificate validity & date verification  │
    └──────────────────────┬───────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │      Cross-Document Discrepancy Auditor      │
    │  Detects conflicting claims between docs     │
    └──────────────────────┬───────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │         Procurement Officer Workbench        │
    │  - Side-by-side evidence inspection          │
    │  - Source page & snippet citations           │
    │  - Manual override & signed audit record     │
    └──────────────────────────────────────────────┘
```

---

## Core Features

- **Hybrid PDF Ingestion**: High-speed text extraction via PyMuPDF with automatic fallback to Tesseract OCR for scanned or rasterized pages.
- **Strict Separation of Concerns**: LLMs extract and structure unstructured text into Pydantic models; deterministic code performs numeric and boolean verification.
- **Pluggable Sector Configurations**: Declarative JSON schemas define sector-specific parameters (e.g. IT Hardware, Civil Works, Medical Supplies), including known certifications (ISO, BIS, MSME, Make-in-India), required specifications, and exemptions.
- **Real-Time Officer Workbench**: Clean React 19 interface displaying side-by-side compliance matrices, conflicting claims, and highlighted document citations.
- **Full Traceability**: Every evaluation outcome points to an exact document, page number, and text excerpt for defensible audit records.

---

## Quick Start

### 1. Run with Docker Compose (Recommended)

Make sure you have [Docker](https://docs.docker.com/get-docker/) installed.

```bash
git clone https://github.com/eswarprasadreddy/tendercheck.git
cd tendercheck

# Configure environment
cp backend/.env.example backend/.env
# Set your GEMINI_API_KEY in backend/.env

# Start PostgreSQL and the backend API
docker compose up --build
```

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 2. Local Development Setup

#### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL 14+ (or run via Docker)
- Tesseract OCR (installed and available on system `PATH`)

#### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\Activate.ps1

# Install package with test dependencies
pip install -e ".[test]"

# Set environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd ../frontend

npm install
npm run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173).

---

### 3. Run the Evaluation Pipeline Demo

TenderCheck includes a standalone pipeline script running synthetic GeM tender evaluations across multiple vendors:

```bash
python demo_data/run_demo_pipeline.py
```

This ingests `demo_data/tender_gem_2026_it_hardware.pdf`, extracts requirements, evaluates Vendor A (fully compliant) and Vendor B (disqualified due to expired ISO certificate and specification contradictions), and prints the verified compliance matrix.

---

## Architecture & Project Structure

```
tendercheck/
├── backend/
│   ├── app/
│   │   ├── api/v1/                # REST route handlers
│   │   │   ├── tenders.py         # Tender upload and clause extraction
│   │   │   ├── vendor_documents.py# Bid packet uploads
│   │   │   ├── matching.py        # Matching & contradiction engine routes
│   │   │   └── reports.py         # Final audit report and officer sign-off
│   │   ├── llm/                   # Gemini 2.0 Flash prompts and client
│   │   ├── models/                # SQLAlchemy 2.0 async ORM models
│   │   ├── schemas/               # Pydantic v2 data transfer schemas
│   │   ├── sectors/               # Sector schemas (e.g., it_hardware.json)
│   │   ├── services/
│   │   │   ├── pdf_extractor.py         # PyMuPDF + Tesseract OCR hybrid pipeline
│   │   │   ├── requirement_parser.py    # Gemini clause parser
│   │   │   ├── matching_engine.py       # Evidence-to-requirement matcher
│   │   │   ├── verification_engine.py   # Deterministic Python rule checks
│   │   │   ├── contradiction_service.py # Cross-document conflict scanner
│   │   │   └── report_service.py        # Report compiler & audit exporter
│   │   ├── config.py              # Application settings
│   │   ├── database.py            # Async engine and session factory
│   │   └── main.py                # FastAPI entry point
│   ├── alembic/                   # Database migrations
│   ├── tests/                     # Unit and integration tests
│   └── pyproject.toml             # Python package configuration
├── frontend/
│   ├── src/
│   │   ├── components/            # Screens: Upload, Requirements, Compliance, Evidence
│   │   ├── api.js                 # API communication layer
│   │   ├── App.jsx                # Application root and state machine
│   │   └── index.css              # Styling tokens
│   └── package.json
├── demo_data/                     # Sample tender & vendor test files
└── docker-compose.yml             # Container orchestration
```

---

## API Reference

Interactive Swagger documentation is available at `/docs` when the backend is running.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/tenders/upload` | Uploads tender PDF, extracts text, and runs clause extraction. |
| `GET` | `/api/v1/tenders/{id}/requirements` | Fetches parsed requirements list with categories and operators. |
| `PUT` | `/api/v1/tenders/{id}/requirements/{req_id}` | Updates or customizes a requirement before evaluation. |
| `POST` | `/api/v1/vendor-docs/upload` | Uploads vendor bid documents (P&L, spec sheets, certificates). |
| `POST` | `/api/v1/matching/run/{tender_id}/{vendor_name}` | Triggers deterministic verification and contradiction analysis. |
| `GET` | `/api/v1/reports/{tender_id}/{vendor_name}` | Retrieves full compliance matrix with citations and discrepancy flags. |
| `POST` | `/report/confirm` | Records officer verdict confirmation, notes, and approval status. |
| `GET` | `/health` | Service health check endpoint. |

---

## Sector Configuration

Sectors are defined declaratively as JSON files in `backend/app/sectors/`. A sector configuration defines the known certificates, standard technical specifications, financial rules, and exemption policies for that domain.

Example snippet from `it_hardware.json`:

```json
{
  "sector_id": "it_hardware",
  "sector_name": "IT Hardware & Electronics Procurement",
  "known_certificates": [
    { "key": "iso_9001", "name": "ISO 9001:2015", "has_expiry": true, "category": "certification" },
    { "key": "bis_registration", "name": "BIS Registration", "has_expiry": true, "category": "certification" },
    { "key": "make_in_india", "name": "Make in India Certificate", "has_expiry": true, "category": "compliance" }
  ],
  "known_specs": [
    { "key": "ram_gb", "name": "RAM", "unit": "GB", "default_operator": ">=" },
    { "key": "ssd_gb", "name": "SSD Storage", "unit": "GB", "default_operator": ">=" },
    { "key": "processor", "name": "Processor", "unit": null, "default_operator": "==" }
  ]
}
```

To support a new sector (e.g., Solar EPC or Medical Supplies), add a new `<sector_id>.json` file and set `SECTOR=<sector_id>` in your environment.

---

## Testing

Backend test suites cover PDF parsing, deterministic rule execution, contradiction detection, and API endpoints:

```bash
cd backend
pytest -v
```

---

## License

This project is licensed under the [MIT License](LICENSE).
