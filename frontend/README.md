<div align="center">

# 💻 TenderCheck Frontend UI

### **High-Performance React 19 Officer Workbench & Evidence Verification Dashboard**

[![React](https://img.shields.io/badge/React-19.3-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)
[![Lucide Icons](https://img.shields.io/badge/Icons-Lucide%20React-F56565?style=flat-square)](https://lucide.dev)
[![Oxlint](https://img.shields.io/badge/Linter-Oxlint-blueviolet?style=flat-square)](https://oxc.rs)

</div>

---

## 📖 Overview

The TenderCheck frontend is a purpose-built procurement officer workbench engineered for rapid document triage, side-by-side compliance verification, and human audit signoff.

### Key Capabilities
- **Tender & Bid Dropzone**: Instant multi-file upload with OCR status indicators and progress telemetry.
- **Requirement Clause Workbench**: Interactive editor to review, refine, or add custom thresholds to tender clauses.
- **Side-by-Side Verification Matrix**: Live color-coded compliance status (Compliant, Non-Compliant, Contradiction, Pending Officer Review).
- **Evidence Panel with Source Citations**: Direct inspection of exact extracted text snippets, matched values, and page coordinates.
- **Authenticated Officer Signoff**: Secure digital review notes, verdict confirmation, and audit report generation.

---

## 📂 Component Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.jsx             # Top app bar with system status & officer identity
│   │   ├── Navigation.jsx         # Step-based workflow progress tracker
│   │   ├── UploadScreen.jsx       # Tender PDF and multi-vendor bid packet ingestion
│   │   ├── RequirementsScreen.jsx # Extracted clause inspector and rule customizer
│   │   ├── ComplianceScreen.jsx   # Vendor qualification grid & discrepancy alerts
│   │   ├── EvidencePanel.jsx      # Page-level citation and document snippet viewer
│   │   └── LoginScreen.jsx        # Procurement officer authentication
│   ├── api.js                     # Unified backend REST client
│   ├── App.jsx                    # Root state machine and step routing
│   ├── index.css                  # Custom tokenized design system (Dark mode first)
│   └── main.jsx                   # React 19 entry point
├── package.json
└── vite.config.js
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18.x or 20.x
- Backend running on `http://localhost:8000`

### Installation & Launch

```bash
# 1. Install dependencies
npm install

# 2. Start Vite development server
npm run dev

# 3. Lint with Oxlint
npm run lint

# 4. Build optimized production bundle
npm run build
```

The app will be accessible at `http://localhost:5173`.
