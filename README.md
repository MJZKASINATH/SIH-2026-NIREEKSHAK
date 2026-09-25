# NIREEKSHAK

**AI-powered MPLADS intelligence platform for detecting anomalies, identifying potential irregularities, and prioritizing public development projects for human review through explainable risk scoring.**

> **SIH 2026 — Problem Statement SIH26102**  
> Team: TrustUs | Version: 2.0.0

---

## Table of Contents

1. [Overview](#1-overview)
2. [Core Workflow](#2-core-workflow)
3. [Key Features](#3-key-features)
4. [User Roles](#4-user-roles)
5. [System Architecture](#5-system-architecture)
6. [Project Structure](#6-project-structure)
7. [Prerequisites](#7-prerequisites)
8. [Quick Start](#8-quick-start)
9. [Fresh ZIP Installation](#9-fresh-zip-installation)
10. [Environment Configuration](#10-environment-configuration)
11. [Database Setup](#11-database-setup)
12. [Dataset Setup](#12-dataset-setup)
13. [Running the Backend](#13-running-the-backend)
14. [Running the Frontend](#14-running-the-frontend)
15. [Running the Complete System](#15-running-the-complete-system)
16. [Demo / Evaluator Login](#16-demo--evaluator-login)
17. [End-to-End Demo Flow](#17-end-to-end-demo-flow)
18. [Risk Scoring](#18-risk-scoring)
19. [AI / Detection Pipeline](#19-ai--detection-pipeline)
20. [Geostat / Map](#20-geostat--map)
21. [API Overview](#21-api-overview)
22. [Testing](#22-testing)
23. [Troubleshooting](#23-troubleshooting)
24. [Security Notes](#24-security-notes)
25. [SIH Demonstration Summary](#25-sih-demonstration-summary)

---

## 1. Overview

### SIH 2026 Problem Statement

NIREEKSHAK was built for **SIH Problem Statement SIH26102**, which requires an intelligent platform to monitor MPLADS (Members of Parliament Local Area Development Scheme) fund utilization, detect anomalous expenditure patterns, and assist government vigilance authorities in identifying projects that warrant closer administrative review.

### What NIREEKSHAK Does

NIREEKSHAK connects real MPLADS project records to a multi-signal AI risk engine that analyses each project across nine independent dimensions — cost benchmarking, tender anomalies, financial vs physical progress gaps, expenditure velocity, geographic verification, duplicate detection, contractor risk history, timeline violations, and cost overrun — then fuses those signals into a single explainable 0–100 risk score.

Projects above the RED_FLAG threshold (≥ 80) automatically generate investigation cases that vigilance auditors can review, annotate, and resolve. Every action — approval, fund release, field evidence upload, investigation note, and resolution — is cryptographically hashed and appended to an immutable audit chain.

### Why the System Is Useful

MPLADS funds approximately ₹5 crore per MP constituency per year. Manual monitoring of thousands of projects spread across India is impractical. NIREEKSHAK automates anomaly detection so that scarce vigilance bandwidth can be directed at the highest-priority cases.

> **Important:** NIREEKSHAK identifies risk signals and anomalies for **human investigation**. A red flag or high risk score is a prioritization signal — it does **not** automatically declare wrongdoing, establish fraud, or constitute a legal finding. Human auditors review the evidence and make all consequential decisions.

---

## 2. Core Workflow

```
MPLADS Raw Data (CSV)
        │
        ▼
Data Ingestion & Cleaning
(NIREEKSHAK-datasets/services/ingestion/)
        │
        ▼
PostgreSQL Database
(trustus — schema created automatically by SQLAlchemy)
        │
        ▼
Project Proposal (MP Role)
        │
        ▼
Identity Verification + Approval (Approving Authority Role)
        │
        ▼
Tender Award (Contractor Registration)
        │
        ▼
Work Execution
  ├── Expenditure Ledger (Financial Transactions)
  ├── Progress Updates (Physical %)
  └── 5 Geo-Tagged Field Checkpoints (GPS + Photo Hash)
        │
        ▼
9-Signal AI Risk Fusion Engine
(Compound 0–100 Risk Score + Explainable Signals)
        │
        ▼
Risk Classification (LOW / MEDIUM / HIGH / RED_FLAG)
        │
        ▼
Red Flag → Automated Investigation Case Opened
        │
        ▼
Human Vigilance Review (Auditor Role)
  ├── Dossier: risk signals, evidence, expenditure
  ├── Investigation notes and clarification requests
  └── Resolution: Cleared / Referred to CBI / Penalty / Closed
        │
        ▼
Immutable Cryptographic Audit Trail
(SHA-256 chained hash — every action logged)
        │
        ▼
Geostatistical Map (All projects, risk-coloured markers)
```

---

## 3. Key Features

All features listed below are implemented in the current repository.

### Project Lifecycle
- **MP Project Proposal**: MPs submit new MPLADS projects with location coordinates, budget estimate, category, and beneficiary details.
- **Identity-Verified Approval**: Approving authorities (IAS/District Magistrate) submit digital signatures and document hashes when sanctioning projects.
- **Tender Management**: Work order assignment to registered contractors with deviation tracking against sanctioned estimates.
- **Expenditure Ledger**: Transaction-level financial records with invoice numbers, document hashes, and cumulative tracking.
- **Progress Updates**: Physical vs financial progress percentages with geo-tagged photos and hashes.
- **5 Geo-Tagged Field Checkpoints**: Each project has five GPS-verified checkpoints (A–E). Each checkpoint records expected vs submitted coordinates, distance deviation, and verification status (VERIFIED / MISMATCH).

### AI Anomaly Detection (9 Independent Engines)
- **Cost Anomaly**: Statistical outlier detection against peer-project category benchmarks.
- **Progress Mismatch**: Flags when financial expenditure substantially leads physical completion.
- **Expenditure Velocity**: Detects abnormal speed of fund disbursement relative to physical progress.
- **Cost Overrun**: Flags when actual expenditure exceeds awarded contract value.
- **Tender Anomaly**: Detects tenders awarded significantly above sanctioned engineering estimates.
- **Duplicate Detection**: Semantic and geographic overlap detection across concurrent projects.
- **Geographic Anomaly**: GPS geofence validation — detects field evidence uploaded far from registered project coordinates.
- **Timeline Anomaly**: Milestone delay detection against expected completion dates.
- **Contractor Risk**: Flags projects awarded to contractors with prior suspicious/flagged project history.

### Risk Intelligence
- Fused 0–100 risk score with multi-signal compounding factor.
- Four-tier classification: LOW / MEDIUM / HIGH / RED_FLAG.
- Human-readable risk summary for every project.
- Automatic investigation case creation at RED_FLAG threshold (≥ 80).

### Investigation Workflow
- Per-project investigation dossier with all risk signals, evidence, transactions, and timeline.
- Investigation case notes: auditor can add clarification requests, findings, escalations, and resolutions.
- Case status tracking: OPEN → UNDER_REVIEW → RESOLVED / REFERRED.
- RBAC enforcement: only AUDITOR and ADMIN roles can manage investigation cases.

### Contractor Intelligence
- Persistent contractor risk profiles: total projects, delayed, suspicious, red-flagged counts.
- Risk status: LOW / MEDIUM / HIGH.
- Associated with projects via tender registration.

### Digital Audit Trail
- Every lifecycle action (proposal, approval, evidence upload, expenditure, investigation note) creates an `AuditLog` record.
- Each record is SHA-256 hashed and chained to the previous record's hash.
- The audit trail is append-only and immutable — deletions are not permitted.

### Geostatistical Map
- Interactive Leaflet map with CARTO basemap tiles.
- All projects with GPS coordinates rendered as coloured markers (green = LOW, yellow = MEDIUM, orange = HIGH, red = RED_FLAG).
- Filters: by state, risk level, contractor, project status, and free-text search.
- Click any marker to view project summary, risk score, expenditure, and navigate to the full dossier.

### Role-Based Access Control (RBAC)
- JWT-based authentication.
- Six roles with different access permissions enforced at the API level.

### Analytics Dashboard
- Live KPI dashboard: total projects, risk distribution, active investigations, total allocation and expenditure.
- Recharts-powered visualizations.

---

## 4. User Roles

The following roles are implemented in the codebase (`lib/auth.ts`, `routes/auth.py`):

| Role | Internal Name | Who They Are | What They Can Do |
|---|---|---|---|
| **Member of Parliament** | `MP` | Elected MP | Propose new MPLADS projects; view own project status |
| **Approving Authority** | `APPROVING_AUTHORITY` | District Magistrate / IAS Officer | Review and approve project proposals; submit identity verification |
| **Contractor** | `CONTRACTOR` | Registered contractor firm | Submit expenditure transactions and progress updates |
| **Field Officer** | `FIELD_OFFICER` | PWD / Inspection Officer | Submit geo-tagged field evidence and checkpoint verifications |
| **Auditor** | `AUDITOR` | CAG / Vigilance Audit Officer | Review investigation cases; add findings; resolve or escalate |
| **Admin** | `ADMIN` | System Administrator | Full access to all system functions and user management |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend — Next.js 16 + TypeScript + Tailwind CSS      │
│  NIREEKSHAK-main/apps/web/                              │
│  Port: 3000                                             │
│  Leaflet (map) · Recharts (analytics) · lucide-react   │
└────────────────────────┬────────────────────────────────┘
                         │  HTTP via next.config.ts rewrite
                         │  /api/* → http://localhost:8000/api/*
┌────────────────────────▼────────────────────────────────┐
│  Backend — FastAPI 0.110+ (Python 3.x)                  │
│  NIREEKSHAK-datasets/apps/api/                          │
│  Port: 8000 · Uvicorn ASGI server                       │
│  SQLAlchemy 2.0 ORM · Pydantic 2 schemas                │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
┌─────────────▼──────┐   ┌──────────▼──────────────────────┐
│  PostgreSQL DB     │   │  AI / Risk Engine                │
│  Database: trustus │   │  services/risk_engine/           │
│  Port: 5432        │   │  9 independent signal modules    │
│  (SQLite fallback) │   │  + risk_fusion.py combinator     │
└────────────────────┘   └──────────────────────────────────┘
                                     │
                         ┌───────────▼────────────┐
                         │  MPLADS Datasets       │
                         │  data/raw/ + processed/│
                         │  ~11MB CSV files       │
                         └────────────────────────┘
```

**Key technology stack:**
- **Frontend**: Next.js 16.3.3, React 19, TypeScript 5, Tailwind CSS 4, Leaflet 1.9, Recharts 2.15
- **Backend**: Python, FastAPI ≥ 0.110, Uvicorn, SQLAlchemy ≥ 2.0, Pydantic ≥ 2.6
- **Database**: PostgreSQL (primary) with automatic SQLite fallback (`nireekshak.db`)
- **Auth**: HMAC-SHA256 JWT tokens; 24-hour expiry
- **Map tiles**: CARTO (no API key required for the tile URLs used)

---

## 6. Project Structure

```
NIREEKSHAK-main/                      ← Repository root
│
├── .env.example                      ← Environment variable template (copy to .env)
├── .gitignore                        ← Excludes secrets, builds, and databases
├── README.md                         ← This file
├── walkthrough.md                    ← Implementation walkthrough
│
├── NIREEKSHAK-datasets/              ← Backend (FastAPI) + Data
│   ├── apps/api/                     ← FastAPI application
│   │   ├── main.py                   ← Application entry point (port 8000)
│   │   ├── database.py               ← DB connection (PostgreSQL + SQLite fallback)
│   │   ├── models.py                 ← SQLAlchemy ORM models
│   │   ├── schemas.py                ← Pydantic request/response schemas
│   │   ├── seed_phase2.py            ← Demo data seeder (runs on startup)
│   │   ├── seed.py                   ← Base MPLADS project seeder
│   │   ├── requirements.txt          ← Python dependencies
│   │   ├── routes/                   ← API route handlers
│   │   │   ├── auth.py               ← Login, RBAC, JWT
│   │   │   ├── lifecycle.py          ← Proposal, approval, tender, expenditure, checkpoints
│   │   │   ├── geostat.py            ← Geostatistical map data endpoint
│   │   │   ├── investigation.py      ← Investigation cases and dossier
│   │   │   ├── analytics.py          ← KPI dashboard data
│   │   │   ├── contractors.py        ← Contractor risk profiles
│   │   │   ├── audit.py              ← Audit trail
│   │   │   ├── projects.py           ← Project list and details
│   │   │   └── risks.py              ← Risk recalculation
│   │   ├── services/
│   │   │   ├── engine.py             ← MPLADS ML engine (parquet/FAISS)
│   │   │   └── risk_engine/          ← 9 independent anomaly detectors + fusion
│   │   │       ├── risk_fusion.py    ← Combines all signals into 0-100 score
│   │   │       ├── cost_anomaly.py
│   │   │       ├── progress_anomaly.py
│   │   │       ├── expenditure_velocity.py
│   │   │       ├── cost_overrun.py
│   │   │       ├── tender_anomaly.py
│   │   │       ├── duplicate_detection.py
│   │   │       ├── geographic_anomaly.py
│   │   │       ├── timeline_anomaly.py
│   │   │       └── contractor_risk.py
│   │   └── tests/
│   │       └── test_phase2_lifecycle.py   ← Integration test suite
│   ├── data/
│   │   ├── raw/mplads_raw.csv             ← Raw MPLADS records (~11 MB, included)
│   │   └── processed/mplads_clean.csv     ← Cleaned dataset (~11.5 MB, included)
│   ├── database/
│   │   ├── schema.sql                     ← PostgreSQL schema definition
│   │   ├── seed.sql                       ← Optional base SQL seed
│   │   └── backup.sql                     ← Reference backup
│   └── services/ingestion/
│       ├── clean.py                       ← Data cleaning pipeline
│       └── load.py                        ← Database ingestion loader
│
└── NIREEKSHAK-main/                  ← Frontend (Next.js)
    └── apps/web/
        ├── package.json              ← npm dependencies
        ├── next.config.ts            ← API rewrite proxy to backend
        ├── app/                      ← Next.js App Router pages
        │   ├── login/page.tsx        ← Login page with demo account quick-fill
        │   ├── dashboard/page.tsx    ← Command centre KPI dashboard
        │   ├── projects/             ← Project list + [id] detail page
        │   ├── geostat/page.tsx      ← Geostatistical map
        │   ├── investigation/        ← Investigation list + [projectId] dossier
        │   ├── contractors/          ← Contractor risk list + [id] profile
        │   ├── audit-logs/page.tsx   ← Audit trail viewer
        │   ├── analytics/page.tsx    ← Analytics and KPI charts
        │   └── reports/page.tsx      ← Reports page
        ├── components/
        │   ├── Sidebar.tsx           ← Navigation sidebar
        │   ├── map/GeostatMap.tsx    ← Leaflet map component
        │   ├── investigation/        ← Dossier, action controls, audit drawer
        │   └── evidence/             ← Risk signal cards
        └── lib/
            ├── auth.ts               ← JWT storage, demo account definitions
            └── anomaly.ts            ← Frontend anomaly utilities
```

---

## 7. Prerequisites

Verify the following are installed before starting.

| Software | Minimum Version | Notes |
|---|---|---|
| **Node.js** | 18.x or higher | 20.x LTS recommended |
| **npm** | 9.x or higher | Included with Node.js |
| **Python** | 3.9 or higher | 3.11 recommended |
| **pip** | Latest | Included with Python |
| **PostgreSQL** | 13 or higher | Required for production use; SQLite fallback available for quick evaluation |

**Optional (for the ML engine in `services/engine.py`):**
- `pandas`, `joblib`, `scikit-learn`, `pyarrow` — these are included in `requirements.txt` and installed with the backend.

---

## 8. Quick Start

For experienced developers. Full detailed instructions are in sections 9–15.

```bash
# 1. Clone / extract the repository
cd NIREEKSHAK-main   # ← the root that contains both NIREEKSHAK-datasets/ and NIREEKSHAK-main/

# 2. Frontend
cd NIREEKSHAK-main/apps/web
npm install
cp ../../.env.example .env.local          # edit NEXT_PUBLIC_BACKEND_URL if needed

# 3. Backend
cd ../../../NIREEKSHAK-datasets/apps/api
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env                # edit DB credentials

# 4. Database (PostgreSQL)
createdb trustus                          # or see Section 11 for manual steps

# 5. Start backend (Terminal 2)
# from NIREEKSHAK-datasets/apps/api, venv active:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 6. Start frontend (Terminal 3)
# from NIREEKSHAK-main/apps/web:
npm run dev

# 7. Open browser
# http://localhost:3000
# Use demo account: mp.demo / Demo@123
```

---

## 9. Fresh ZIP Installation

### Step 1 — Download and Extract

Download the repository ZIP from GitHub:  
`https://github.com/jeevanjacob1/SIH-2026-NIREEKSHAK`

Extract the ZIP. You should see a folder structure containing:
```
NIREEKSHAK-main/
├── NIREEKSHAK-datasets/
├── NIREEKSHAK-main/
├── .env.example
├── .gitignore
└── README.md
```

Open a terminal in the extracted `NIREEKSHAK-main/` directory.

---

### Step 2 — Install Frontend Dependencies

```bash
cd NIREEKSHAK-main/apps/web
npm install
```

This installs Next.js, React, Leaflet, Recharts, and all other frontend packages.

---

### Step 3 — Set Up Python Environment for Backend

```bash
cd ../../..                              # back to NIREEKSHAK-main/ root
cd NIREEKSHAK-datasets/apps/api
python -m venv .venv
```

**Activate the virtual environment:**

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (Command Prompt):** `.venv\Scripts\activate.bat`
- **macOS / Linux:** `source .venv/bin/activate`

Your prompt should now show `(.venv)`.

---

### Step 4 — Install Backend Dependencies

With the virtual environment active:

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, SQLAlchemy, psycopg2-binary, pandas, scikit-learn, and related packages.

---

### Step 5 — Configure Environment Variables

From the repository root (`NIREEKSHAK-main/`):

```bash
cp .env.example .env
```

Edit `.env` with your database credentials. See [Section 10](#10-environment-configuration) for all variables.

Also create the frontend environment file:

```bash
cd NIREEKSHAK-main/apps/web
```

Create a file named `.env.local` in that directory with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Or copy from the root `.env.example` for reference.

---

### Step 6 — Set Up PostgreSQL Database

See [Section 11](#11-database-setup) for full details. Quick summary:

```bash
# Create the database (run in your PostgreSQL client or terminal):
createdb -U postgres trustus
```

The schema and initial data are created **automatically** when the backend starts for the first time.

---

### Step 7 — Start the Backend

From `NIREEKSHAK-datasets/apps/api/` with the virtual environment active:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup, the backend will:
1. Create all database tables (via SQLAlchemy `create_all`).
2. Apply any schema migrations for Phase 2 fields.
3. Seed the demonstration dataset (6 scenario projects, 6 demo users, risk profiles, investigation cases, checkpoints, expenditures).

You should see:
```
Initializing NIREEKSHAK Phase 2 Core...
Connected to PostgreSQL database: localhost:5432/trustus
Database schema verified/created successfully.
Seeding NIREEKSHAK Phase 2 Demonstration Dataset...
NIREEKSHAK Phase 2 Demonstration Dataset seeded successfully!
NIREEKSHAK Phase 2 Core Operational.
```

---

### Step 8 — Start the Frontend

Open a **new terminal**, navigate to `NIREEKSHAK-main/apps/web/`:

```bash
npm run dev
```

The frontend starts on port 3000.

---

### Step 9 — Open the Application

Open your browser and go to: **http://localhost:3000**

You will be redirected to the login page. Use any of the demo accounts from [Section 16](#16-demo--evaluator-login).

---

## 10. Environment Configuration

The repository includes `.env.example` at the root level. **Never commit a real `.env` or `.env.local` file** — these are excluded by `.gitignore`.

Create your own `.env` in `NIREEKSHAK-datasets/apps/api/` and `.env.local` in `NIREEKSHAK-main/apps/web/` based on this template.

### Backend Environment Variables

| Variable | Purpose | Used In | Required | Example Value |
|---|---|---|---|---|
| `DB_USER` | PostgreSQL username | `database.py` | Yes (for PostgreSQL) | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `database.py` | Yes (for PostgreSQL) | `yourpassword` |
| `DB_HOST` | PostgreSQL host | `database.py` | Yes (for PostgreSQL) | `localhost` |
| `DB_PORT` | PostgreSQL port | `database.py` | Yes (for PostgreSQL) | `5432` |
| `DB_NAME` | PostgreSQL database name | `database.py` | Yes (for PostgreSQL) | `trustus` |
| `DATABASE_URL` | Override full connection string | `database.py` | No | `postgresql://postgres:pass@localhost:5432/trustus` |
| `JWT_SECRET_KEY` | HMAC-SHA256 signing key for JWT tokens | `routes/auth.py` | Yes | Use a long random string in production |
| `JWT_ALGORITHM` | JWT signing algorithm | Reference only | No | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token validity in minutes | Reference only | No | `1440` |
| `FASTAPI_HOST` | Uvicorn bind host | Reference only | No | `0.0.0.0` |
| `FASTAPI_PORT` | Uvicorn bind port | Reference only | No | `8000` |

### Frontend Environment Variables

| Variable | Purpose | Used In | Required | Example Value |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL for API calls from the browser | Frontend fetch calls | Yes | `http://localhost:8000/api` |
| `NEXT_PUBLIC_BACKEND_URL` | Backend origin for Next.js API rewrite | `next.config.ts` | Yes | `http://localhost:8000` |

> **Note:** `.env` and `.env.local` files are intentionally excluded from this repository. The `.env.example` file is the only template — copy and fill it with your own values. Do not commit real credentials.

---

## 11. Database Setup

### PostgreSQL (Recommended)

PostgreSQL 13 or higher is required for the full application. The database name used by the application is **`trustus`**.

**Step 1 — Create the database:**

```bash
# Using the psql command-line client:
psql -U postgres -c "CREATE DATABASE trustus;"
```

Or using the `createdb` utility:

```bash
createdb -U postgres trustus
```

**Step 2 — Configure credentials:**

Set `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME` in your `.env` file (see Section 10).

**Step 3 — Start the backend:**

```bash
# From NIREEKSHAK-datasets/apps/api/ with venv active:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend automatically runs:
- `Base.metadata.create_all(bind=engine)` — creates all tables from SQLAlchemy models.
- PostgreSQL `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` migrations for Phase 2 fields.
- `seed_demo_data()` — seeds demo users, projects, risk profiles, investigation cases, and checkpoints if they do not already exist (idempotent).

The `database/schema.sql` file is an alternative reference that can be applied manually:

```bash
psql -U postgres -d trustus -f NIREEKSHAK-datasets/database/schema.sql
psql -U postgres -d trustus -f NIREEKSHAK-datasets/database/seed.sql  # optional base records
```

### SQLite Fallback

If PostgreSQL is unavailable, the backend automatically falls back to a local SQLite database (`nireekshak.db`) created in `NIREEKSHAK-datasets/apps/api/`. This is suitable for quick local evaluation but is **not recommended for production or multi-user scenarios**.

The SQLite fallback is fully automatic — no additional configuration is required.

---

## 12. Dataset Setup

### What Is Already Included

The repository includes the following dataset files:

| File | Size | Description |
|---|---|---|
| `NIREEKSHAK-datasets/data/raw/mplads_raw.csv` | ~11 MB | Original MPLADS project records |
| `NIREEKSHAK-datasets/data/processed/mplads_clean.csv` | ~11.5 MB | Cleaned and preprocessed MPLADS data |

**You do not need to download any additional data files.** Both CSV files are already present in the repository.

### Demo Scenario Projects

The backend `seed_phase2.py` script seeds **6 carefully designed scenario projects** directly from code at startup. These are the primary projects used in the evaluation demo and map visualization. They represent:
1. A normal low-risk project (Kerala, road construction).
2. A cost anomaly / tender inflation project (Tamil Nadu, health centre).
3. A progress mismatch red-flag project (Uttar Pradesh, skill centre).
4. A contractor risk red-flag project (Karnataka, water plant).
5. A geographic anomaly / GPS mismatch project (Maharashtra, school lab).
6. A multi-anomaly compound red-flag project (Kerala, coastal shelter).

### Ingestion Scripts (Optional)

The `NIREEKSHAK-datasets/services/ingestion/` scripts (`clean.py`, `load.py`) can be used to re-process the raw CSV into the database. These are optional and not required for the demo — the automatic seeder covers evaluation needs.

---

## 13. Running the Backend

**Directory:** `NIREEKSHAK-datasets/apps/api/`

**Activate virtual environment first** (see Step 3 in Section 9).

**Start command:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

| Property | Value |
|---|---|
| Host | `0.0.0.0` (all interfaces) |
| Port | `8000` |
| API base URL | `http://localhost:8000/api` |
| Interactive API docs | `http://localhost:8000/docs` (Swagger UI) |
| Health check | `http://localhost:8000/api/health` |

The `--reload` flag enables auto-restart on code changes (development mode). Remove it for production.

---

## 14. Running the Frontend

**Directory:** `NIREEKSHAK-main/apps/web/`

**Install dependencies (first time only):**

```bash
npm install
```

**Start development server:**

```bash
npm run dev
```

| Property | Value |
|---|---|
| Port | `3000` |
| Browser URL | `http://localhost:3000` |
| API proxy | All `/api/*` requests are forwarded to `http://localhost:8000/api/*` via `next.config.ts` |

The frontend will not function without the backend running.

---

## 15. Running the Complete System

Use three separate terminals.

### Terminal 1 — PostgreSQL

Ensure PostgreSQL is running on port 5432 with the `trustus` database created. On most systems:

```bash
# macOS (Homebrew):
brew services start postgresql

# Linux (systemd):
sudo systemctl start postgresql

# Windows:
# Start PostgreSQL from Services or pgAdmin
```

### Terminal 2 — Backend

```bash
cd NIREEKSHAK-datasets/apps/api
# Activate venv:
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Wait until you see `NIREEKSHAK Phase 2 Core Operational.` before starting the frontend.

### Terminal 3 — Frontend

```bash
cd NIREEKSHAK-main/apps/web
npm run dev
```

### Open the Application

**http://localhost:3000**

---

## 16. Demo / Evaluator Login

The following accounts are seeded automatically on first backend startup. All use the password **`Demo@123`**.

The login page includes a **one-click quick-fill panel** for all demo accounts — no typing required.

| Display Name | Username | Password | Role |
|---|---|---|---|
| Rahul Verma (MP) | `mp.demo` | `Demo@123` | `MP` |
| Dr. Rajesh Sharma, IAS | `authority.demo` | `Demo@123` | `APPROVING_AUTHORITY` |
| Vikramaditya Rao (Apex Infra) | `contractor.demo` | `Demo@123` | `CONTRACTOR` |
| Suresh Patel (PWD Engineer) | `field.demo` | `Demo@123` | `FIELD_OFFICER` |
| Anita Verma (CAG Auditor) | `auditor.demo` | `Demo@123` | `AUDITOR` |
| National Administrator | `admin.demo` | `Demo@123` | `ADMIN` |

> These are demonstration credentials for local evaluation only. Do not use them in production.

---

## 17. End-to-End Demo Flow

The following sequence demonstrates the complete implemented lifecycle using the seeded demo data.

### Step 1 — Login as MP

1. Open `http://localhost:3000`.
2. Click the **MP** quick-fill button on the login page.
3. Click **Authenticate & Access System**.

### Step 2 — View the Dashboard

The command-centre dashboard shows live KPIs:
- Total projects, active projects, risk distribution.
- Total allocation and expenditure.
- Active investigation count.

### Step 3 — View Projects

Navigate to **Projects** in the sidebar. The seeded demo projects are listed. Each shows project ID, title, category, status, and risk level.

### Step 4 — Propose a New Project

On the Projects page, click **Propose New Project**. Fill in:
- Title, description, category.
- State, district, constituency.
- Proposed amount and expected completion date.
- Latitude and longitude (GPS coordinates).
- Beneficiary information.

Submit. The new project appears in the list with status `SUBMITTED`.

### Step 5 — Login as Approving Authority

Log out and log back in as `authority.demo`. Navigate to Projects and find the proposed project.

Open it. The approval panel allows submitting:
- Approval remarks.
- Digital signature hash.
- Identity document hash.
- GPS confirmation coordinates.

Submit approval. Project status becomes `APPROVED`.

### Step 6 — Login as Contractor

Log in as `contractor.demo`. Navigate to Projects → the approved project.

Submit:
- **Expenditure transactions**: category, description, amount, invoice number.
- **Progress updates**: physical % completion, financial % completion, geo-tagged photo.

### Step 7 — Login as Field Officer

Log in as `field.demo`. Open the project. Submit GPS-tagged field evidence for each of the 5 checkpoints (A–E), including photo hash and location coordinates.

### Step 8 — View AI Risk Score

Return to the project detail page (any role). The **Risk Analysis** panel shows:
- Compound risk score (0–100).
- Risk level (LOW / MEDIUM / HIGH / RED_FLAG).
- Individual signal cards explaining each detected anomaly.
- Human-readable risk summary.

### Step 9 — Inspect a Pre-Seeded Red Flag

Navigate to **Projects** and open `MPLADS-2026-UP-000303` (Varanasi Skill Centre) or `MPLADS-2026-KL-000606` (Ernakulam Coastal Centre). These are pre-seeded with RED_FLAG status and compound signals.

### Step 10 — Investigation Dossier

Navigate to **Investigation** in the sidebar. Open a RED_FLAG case.

The investigation dossier shows:
- Risk signals with evidence.
- Expenditure ledger.
- Progress vs financial divergence.
- Geo-checkpoint verification statuses.
- Contractor risk profile.

### Step 11 — Auditor Action

Log in as `auditor.demo`. Open the investigation case. Add an investigation note (e.g., clarification request). Change the case status (OPEN → UNDER_REVIEW → RESOLVED).

### Step 12 — Audit Trail

Navigate to **Audit Logs** in the sidebar. View the immutable chain of all actions taken in the current session and from the seeded data. Each entry shows: action type, actor, project, timestamp, and hash.

### Step 13 — Geostatistical Map

Navigate to **Geostat Map**. The Leaflet map shows all 6 seeded demo projects (and any additional seeded projects from `seed.py`) as coloured markers across India.

- Click any marker to see project summary, risk score, and expenditure.
- Use the filters to view by state, risk level, contractor, or search by project ID.
- Click **View Full Dossier** in the popup to go directly to the investigation/project page.

---

## 18. Risk Scoring

### Score Range and Classification

Risk scores are computed by the `calculate_fused_risk()` function in `services/risk_engine/risk_fusion.py`.

| Score Range | Risk Level | Meaning |
|---|---|---|
| 0 – 29 | `LOW` | Parameters within standard MPLADS benchmarks |
| 30 – 59 | `MEDIUM` | Minor variances detected; continuous monitoring advised |
| 60 – 79 | `HIGH` | Anomalous indicators requiring administrative review |
| 80 – 100 | `RED_FLAG` | Compound signals; automatic investigation case opened |

### Multi-Signal Compounding

When three or more independent signals are active simultaneously, the score is multiplied by a **1.15 compounding factor** (capped at 100). This reflects the statistical improbability of multiple concurrent anomalies occurring by chance.

### What a Red Flag Means

A RED_FLAG score means the project has crossed the automated threshold for human review. An investigation case is opened automatically. The auditor reviews the evidence and makes all consequential decisions.

> **A red flag does not establish fraud, wrongdoing, or legal liability.** It is a prioritization signal for human investigation.

---

## 19. AI / Detection Pipeline

Nine independent anomaly detectors are implemented in `NIREEKSHAK-datasets/apps/api/services/risk_engine/`.

| Engine | File | What It Detects | Evidence Used |
|---|---|---|---|
| **Cost Anomaly** | `cost_anomaly.py` | Project cost is a statistical outlier vs peer category median | `awarded_amount` vs peer IQR benchmarks |
| **Progress Mismatch** | `progress_anomaly.py` | Financial expenditure substantially leads physical completion | `financial_progress_percent` vs `physical_progress_percent` |
| **Expenditure Velocity** | `expenditure_velocity.py` | Abnormally fast fund disbursement relative to work completion | Transaction timestamps and cumulative amounts |
| **Cost Overrun** | `cost_overrun.py` | Actual expenditure exceeds awarded contract amount | `expenditure_amount` vs `awarded_amount` |
| **Tender Anomaly** | `tender_anomaly.py` | Tender awarded well above sanctioned engineering estimate | `tender_deviation_percent` |
| **Duplicate Detection** | `duplicate_detection.py` | Semantic and geographic overlap with concurrent projects | Description text similarity + GPS proximity |
| **Geographic Anomaly** | `geographic_anomaly.py` | Field evidence uploaded far from registered project location | GPS checkpoint `distance_meters` and geofence radius |
| **Timeline Anomaly** | `timeline_anomaly.py` | Project overdue relative to expected completion date | `completion_date` vs `expected_completion_date` |
| **Contractor Risk** | `contractor_risk.py` | Contractor has prior suspicious/flagged project history | `ContractorRiskProfile` fields |

Each engine returns a boolean flag, a `scoreImpact` value (points added to total risk), and a human-readable signal description. The `risk_fusion.py` combinator aggregates all nine signals, applies the compounding factor, and produces the final score and classification.

---

## 20. Geostat / Map

### What the Map Shows

The Geostatistical Map (`/geostat`) displays all database projects that have valid latitude and longitude coordinates as interactive markers on a Leaflet map with CARTO basemap tiles.

### Marker Colors

| Color | Risk Level |
|---|---|
| Green | LOW (0–29) |
| Yellow | MEDIUM (30–59) |
| Orange | HIGH (60–79) |
| Red | RED_FLAG (≥ 80) or project status is `RED_FLAGGED` |

### Data Source

The map queries `GET /api/geostat/projects`, which returns real database records with no mock data. Each marker includes:
- Project ID and title
- Risk score and level
- Awarded amount and expenditure
- Physical progress percentage
- Financial utilization percentage
- State, district, constituency
- Contractor name
- Verified / total checkpoint counts

### Filters

The map sidebar supports filtering by:
- **State** (populated from actual project data)
- **Risk Level** (ALL / LOW / MEDIUM / HIGH / RED_FLAG)
- **Contractor** (populated from actual project data)
- **Project Status**
- **Free-text Search** (matches project ID, title, contractor name, constituency)

### Map Configuration

The map uses CARTO tile URLs directly — no API key configuration is required for the tile layer used.

---

## 21. API Overview

All routes are under the `/api` prefix. Interactive documentation is available at `http://localhost:8000/docs`.

| Route Group | Prefix | Description |
|---|---|---|
| Authentication | `/api/auth` | Login (`POST /api/auth/login`), current user (`GET /api/auth/me`) |
| Projects | `/api/projects` | List, detail, proposal, approval, tender, expenditure, progress, checkpoints |
| Lifecycle | `/api/projects` | Proposal, approval, evidence upload, geo-checkpoint submission |
| Geostat | `/api/geostat` | `GET /api/geostat/projects` — map data with filters |
| Investigation | `/api/investigation`, `/api/cases` | Case list, dossier detail, investigation notes |
| Analytics | `/api/analytics` | `GET /api/analytics/overview` — live KPI dashboard data |
| Contractors | `/api/contractors` | Contractor risk profiles |
| Audit | `/api/audit` | Audit log trail |
| Risks | `/api/risks` | Risk recalculation endpoint |
| Health | `/api/health` | System health check |

---

## 22. Testing

### Integration Test Suite

The backend includes a test suite in `NIREEKSHAK-datasets/apps/api/tests/test_phase2_lifecycle.py`.

**To run:**

```bash
cd NIREEKSHAK-datasets/apps/api
# Activate your virtual environment first
python -m pytest tests/test_phase2_lifecycle.py -v
```

Or using unittest directly:

```bash
python -m unittest tests/test_phase2_lifecycle.py -v
```

**Tested areas include:**
- System health check endpoint.
- Demo credential authentication (all six roles).
- Project proposal via MP role.
- Project approval via Approving Authority role.
- Tender award.
- Expenditure submission.
- Progress update submission.
- Geo-checkpoint submission and GPS validation.
- AI risk score calculation and threshold classification.
- Investigation case creation and note submission.
- RBAC enforcement (verifying unauthorized roles are rejected with 403).
- Audit log chain integrity.

### Adversarial Hardening Tests

A separate adversarial test script is available at `scratch/test_adversarial_hardening.py` (in the repository root's `scratch/` folder — note this folder is excluded from git by `.gitignore`). This script validates 25 security and business logic requirements including:
- Negative expenditure rejection.
- Invalid GPS coordinate rejection.
- Unauthorized role access (403 enforcement).
- Duplicate seeding idempotency.
- Audit chain hash integrity.

---

## 23. Troubleshooting

### PostgreSQL Connection Failed

**Symptom:** Backend prints `Database connection attempt failed for postgresql://...`

**Solutions:**
- Ensure PostgreSQL service is running.
- Verify `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` in your `.env` file match your local PostgreSQL setup.
- Check that the `trustus` database exists: `psql -U postgres -l`.
- If PostgreSQL is unavailable, the backend will automatically fall back to SQLite. Check the startup log for `Connected to SQLite fallback database`.

### Backend Not Starting — Missing `.env`

**Symptom:** `KeyError` or database connection errors on startup.

**Solution:** Ensure you have created a `.env` file in `NIREEKSHAK-datasets/apps/api/` (copy from `.env.example` in the root).

### Frontend Shows "Failed to fetch" or Network Errors

**Symptom:** API calls return network errors in the browser.

**Solutions:**
- Confirm the backend is running on port 8000: visit `http://localhost:8000/api/health`.
- Ensure `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` is set in `.env.local` inside `NIREEKSHAK-main/apps/web/`.
- Restart `npm run dev` after editing `.env.local`.

### Port Already in Use

**Symptom:** `EADDRINUSE: address already in use :::3000` or `ERROR: [Errno 10048] ...8000`.

**Solutions:**
- Stop the existing process using that port, or change the port:
  - Frontend: `npm run dev -- -p 3001`
  - Backend: `uvicorn main:app --port 8001`
- If changing the backend port, update `NEXT_PUBLIC_BACKEND_URL` accordingly.

### npm Installation Failures

**Symptom:** `npm install` fails with peer dependency errors.

**Solution:**
```bash
npm install --legacy-peer-deps
```

### Python Dependency Errors

**Symptom:** `ModuleNotFoundError` when starting uvicorn.

**Solutions:**
- Ensure your virtual environment is **activated** before running `pip install` and `uvicorn`.
- Run `pip install -r requirements.txt` again.
- Try `pip install --upgrade pip` then `pip install -r requirements.txt`.

### Database Schema Errors

**Symptom:** `column "project_title" of relation "projects" does not exist`.

**Solution:** The backend applies `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` migrations on startup. Restart the backend — it should apply the missing columns automatically.

### Map Shows No Markers

**Symptom:** Geostat map is empty.

**Solutions:**
- Verify the backend is running and `http://localhost:8000/api/geostat/projects` returns data.
- Confirm the demo data was seeded: the startup log should show `NIREEKSHAK Phase 2 Demonstration Dataset seeded successfully!`
- Check browser console for errors.

### Demo Data Not Seeded

**Symptom:** Login fails or no projects visible.

**Solution:** The seeder runs once on first startup and skips if data already exists. If it did not run:
```bash
cd NIREEKSHAK-datasets/apps/api
# venv active:
python seed_phase2.py
```

---

## 24. Security Notes

- **Never commit `.env` or `.env.local` files.** These are excluded by `.gitignore` for this reason. Use `.env.example` as your template.
- The default `JWT_SECRET_KEY` in `.env.example` is a placeholder for demonstration. **Change it to a strong random secret before any production or shared deployment.**
- Demo credentials (`Demo@123`) are for local evaluation only. They should never be used in a real government deployment.
- Database credentials should be supplied by the deploying administrator and must not be hardcoded in source files.
- The NIREEKSHAK platform provides **risk intelligence and human-review prioritization**. It does not constitute automatic legal determination of fraud, misappropriation, or criminal liability. All consequential decisions are made by authorized human officers.

---

## 25. SIH Demonstration Summary

### How NIREEKSHAK Addresses SIH26102

NIREEKSHAK directly addresses the SIH26102 requirement to build an intelligent monitoring system for MPLADS fund utilization by delivering a complete, end-to-end platform that:

1. **Ingests real MPLADS data** — 60,000+ project records from the included CSV datasets.

2. **Models the full project lifecycle** — from MP proposal → identity-verified approval → contractor tender → field execution → financial transactions → GPS-verified checkpoints.

3. **Applies nine independent AI detectors** — cost benchmarking, progress divergence, expenditure velocity, contract overrun, tender inflation, duplicate overlap, GPS geofence validation, timeline delay, and contractor risk history — against each project independently.

4. **Fuses signals into a single explainable score** — the 0–100 compound risk score is transparent: every point is attributed to a named signal with a human-readable description. No black-box outputs.

5. **Automatically escalates high-priority cases** — projects scoring RED_FLAG (≥ 80) trigger automatic investigation case creation, ensuring vigilance resources are directed where the statistical risk concentration is highest.

6. **Supports the complete human review chain** — auditors receive a full dossier, can add investigation notes, request clarifications, and record resolutions. The platform supports decision-making without replacing it.

7. **Maintains an immutable audit trail** — every action is SHA-256 hashed and chained, providing a tamper-evident record of all decisions for accountability and RTI compliance.

8. **Visualizes national coverage** — the geostatistical map shows the geographic distribution of risk across India, enabling systemic pattern identification that would be invisible in tabular reports.

The result is a system that turns thousands of unmonitored MPLADS records into a **ranked, explainable, human-reviewable watchlist** — making the finite vigilance capacity of government audit offices dramatically more effective.

---

*NIREEKSHAK — Team TrustUs | SIH 2026 | Problem Statement SIH26102*
