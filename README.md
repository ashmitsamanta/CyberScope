# CYBERSCOPE

### Explainable Cyber-Fraud Intelligence & Investigation Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?style=flat&logo=React&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg?style=flat&logo=TypeScript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![NetworkX](https://img.shields.io/badge/Graph-NetworkX-blue.svg?style=flat)](https://networkx.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> *"Fraud does not happen as one isolated event. It appears as a chain of connected evidence. CYBERSCOPE reconstructs that chain."*

---

## 1. Project Overview

**CYBERSCOPE** is a defensive, explainable cyber-fraud intelligence and investigation console designed for security operations centers (SOCs), financial fraud analysts, and incident response teams.

Traditional anti-fraud systems evaluate suspicious events in isolation (such as an individual phishing complaint or a single anomalous transfer). CYBERSCOPE reconstructs the complete evidence chain:
- Ingests raw unstructured scam evidence (SMS, complaints, web forms).
- Extracts and normalizes digital identifiers (phones, domains, UPI IDs, bank accounts).
- Connects fragmented entities into an interactive, multi-hop **Fraud Graph**.
- Computes an **Explainable Investigation Risk Score** (0–100) with transparent, itemized contributing signals.
- Detects coordinated cybercrime campaigns sharing underlying attack infrastructure.
- Traces simulated money movement through complex mule networks (layering, fan-out, circular loops).
- Powers an evidence-grounded AI assistant (**CYBER-ASSIST**) that provides actionable, citation-backed investigative answers grounded in observed database records.

---

## 2. Safety & Scope Disclaimer

> **IMPORTANT DEFENSIVE RESEARCH NOTICE:**  
> **CYBERSCOPE is a defensive research and hackathon prototype using synthetic, fictional data only.**  
> It does not connect to real bank accounts, real payment gateways, or live telecommunication carriers. Risk scores are investigative signals intended for analyst prioritization, not legal proof of criminal activity.

---

## 3. High-Level Architecture

```
                       SYNTHETIC DATA INGESTION
                                  ↓
      ┌────────────────────────────────────────────────────────┐
      │         Entity Extraction & Normalization Engine       │
      │  (Regex + Normalization for Phone, Domain, UPI, IFSC)  │
      └───────────────────────────┬────────────────────────────┘
                                  ↓
      ┌────────────────────────────────────────────────────────┐
      │             In-Memory Fraud Graph (NetworkX)           │
      │   (Hops, Shortest Paths, Cycles, Shared Infrastructure)│
      └───────┬───────────────────┬───────────────────┬────────┘
              │                   │                   │
              ↓                   ↓                   ↓
      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
      │ Explainable  │    │  Campaign    │    │  Money-Flow  │
      │ Risk Engine  │    │  Detector    │    │ Trace Engine │
      │  (Max 100)   │    │ (Clustering) │    │  (BFS Hops)  │
      └───────┬──────┘    └──────┬───────┘    └──────┬───────┘
              │                  │                   │
              └──────────────────┼───────────────────┘
                                 ↓
      ┌────────────────────────────────────────────────────────┐
      │           CYBER-ASSIST Grounded AI Investigator        │
      │    (Deterministic Evidence Grounding + Citations)      │
      └──────────────────────────┬─────────────────────────────┘
                                 ↓
      ┌────────────────────────────────────────────────────────┐
      │          Analyst Console (React + Vite + Tailwind)     │
      │    (Overview, Cases, Graph, Entities, Trace, Workspace)│
      └────────────────────────────────────────────────────────┘
```

---

## 4. Complete Project File Structure

```text
CYBERSCOPE/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── campaigns.py          # Coordinated fraud campaign clustering endpoints
│   │   │   ├── cases.py              # Case management, filtering, and report ingestion
│   │   │   ├── entities.py           # 360-degree entity lookup and neighbor exploration
│   │   │   ├── graph.py              # Interactive fraud graph & circular flow endpoints
│   │   │   ├── health.py             # Health check & defensive scope disclaimer
│   │   │   ├── investigations.py     # CYBER-ASSIST AI investigator & summary brief
│   │   │   ├── search.py             # Safe controlled natural-language search
│   │   │   ├── stats.py              # Platform KPI aggregations for SOC dashboard
│   │   │   └── transactions.py       # Ledger exploration and recursive fund tracing
│   │   ├── analyzers/
│   │   │   ├── __init__.py           # Package exports for analyzers
│   │   │   ├── behavioral_analyzer.py # Burst velocity, fan-out/in, dormancy-to-burst
│   │   │   ├── communication_analyzer.py # Impersonation, urgency, credential harvesting
│   │   │   ├── graph_analyzer.py     # NetworkX topology, cycles, shortest paths
│   │   │   └── transaction_analyzer.py # High-value, structuring, and counterparty risk
│   │   ├── models/
│   │   │   ├── __init__.py           # Package exports for ORM models
│   │   │   ├── base.py               # Base class & timestamp mixin
│   │   │   ├── campaign.py           # Campaign ORM model
│   │   │   ├── case.py               # Case ORM model with metadata
│   │   │   ├── entity.py             # Entity ORM model (phones, accounts, domains)
│   │   │   ├── indicator.py          # Indicator ORM model
│   │   │   ├── investigation.py      # Investigation log ORM model
│   │   │   ├── message.py            # Communication records (SMS/email)
│   │   │   ├── relationship.py       # Graph edges & multi-hop connections
│   │   │   └── transaction.py        # Financial ledger transactions
│   │   ├── schemas/
│   │   │   ├── __init__.py           # Package exports for Pydantic schemas
│   │   │   ├── campaign.py           # Campaign serialization schemas
│   │   │   ├── case.py               # Case detail, list, update & risk signal schemas
│   │   │   ├── entity.py             # Entity detail & neighbor response schemas
│   │   │   ├── graph.py              # GraphNode, GraphEdge & filter schemas
│   │   │   ├── investigation.py      # AI query, citations & timeline event schemas
│   │   │   └── transaction.py        # Transaction & money-flow trace schemas
│   │   ├── services/
│   │   │   ├── ai_service.py         # AIProvider abstraction (Deterministic + OpenAI)
│   │   │   ├── campaign_service.py   # Multi-incident syndicate clustering service
│   │   │   ├── entity_service.py     # Deduplication, resolution, and relational indexing
│   │   │   ├── graph_service.py      # In-memory NetworkX synchronized graph engine
│   │   │   ├── ingestion_service.py  # Regex extraction & automatic graph link creation
│   │   │   ├── risk_service.py       # Transparent explainable scoring engine (Max 100)
│   │   │   ├── timeline_service.py   # Chronological evidence sequencing service
│   │   │   └── transaction_service.py# Recursive BFS money-flow trace engine
│   │   ├── utils/
│   │   │   └── normalization.py      # E.164 phone, domain, URL, and UPI normalizers
│   │   ├── config.py                 # Pydantic BaseSettings with environment overrides
│   │   ├── database.py               # Session lifecycle (SQLite default / PostgreSQL)
│   │   └── main.py                   # FastAPI lifespan, CORS, and centralized routing
│   ├── scripts/
│   │   ├── generate_dataset.py       # Deterministic generator (Seed 42, 9 patterns)
│   │   ├── seed_demo.py              # Populates database with "Operation Phantom KYC"
│   │   ├── reset_demo.py             # One-command demo reset utility
│   │   └── evaluate_patterns.py      # Benchmark evaluation (Regression + Held-Out Noisy)
│   ├── tests/
│   │   ├── test_analyzers.py         # Unit tests for heuristics, normalization & ReDoS
│   │   └── test_api.py               # REST API integration tests & security checks (20/20)
│   ├── Dockerfile                    # Python 3.11 container build definition
│   └── requirements.txt              # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CyberAssistChat.tsx   # Grounded AI assistant with prompt pills & citations
│   │   │   ├── GraphViewer.tsx       # Interactive SVG/Canvas graph (zoom, pan, drag)
│   │   │   ├── MoneyFlowViewer.tsx   # Visual multi-hop fund movement diagram
│   │   │   ├── Navbar.tsx            # Console navigation, status badges & search trigger
│   │   │   ├── RiskScoreBadge.tsx    # Color-coded risk meter (LOW/MED/HIGH/CRITICAL)
│   │   │   ├── SearchModal.tsx       # Natural language controlled query interface
│   │   │   └── TimelineView.tsx      # Chronological incident stream
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx     # Overview: KPIs, risk spectrum, campaigns, queue
│   │   │   ├── CasesPage.tsx         # Filterable case registry with search
│   │   │   ├── GraphPage.tsx         # Full-network graph explorer & cycle detector
│   │   │   ├── EntityExplorerPage.tsx# 360-degree entity dossier & neighbor hops
│   │   │   ├── TransactionsPage.tsx  # Tabular ledger & modal fund tracing
│   │   │   ├── CampaignsPage.tsx     # Syndicate clusters & shared fingerprints
│   │   │   └── InvestigationWorkspacePage.tsx # Flagship 4-quadrant demo workspace
│   │   ├── services/
│   │   │   └── api.ts                # Typed fetch API client
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript interfaces matching backend models
│   │   ├── App.tsx                   # Top-level state and routing
│   │   ├── index.css                 # Dark SOC theme styling & custom scrollbars
│   │   └── main.tsx                  # React 18 DOM root
│   ├── Dockerfile                    # Multi-stage Node builder & Nginx runner
│   ├── nginx.conf                    # Nginx reverse proxy configuration
│   ├── package.json                  # Frontend dependencies and build scripts
│   ├── postcss.config.js             # PostCSS Tailwind plugins
│   ├── tailwind.config.js            # SOC dark color tokens & fonts
│   ├── tsconfig.json                 # TypeScript compiler options
│   └── vite.config.ts                # Vite config with API proxy
├── data/
│   └── synthetic/
│       └── benchmark_dataset.json    # Exported benchmark dataset
├── docs/
│   ├── api.md                        # Full REST API specification
│   ├── architecture.md               # Technical subsystem design
│   ├── demo-script.md                # 3-minute hackathon walkthrough script
│   └── detection-methodology.md      # Mathematical & heuristic fraud formulas
├── .env                              # Active environment configuration
├── .env.example                      # Environment variables template
├── .gitignore                        # Git exclusion rules
├── docker-compose.yml                # Multi-container orchestration (Postgres, App, Nginx)
├── LICENSE                           # MIT License
├── Makefile                          # Unified build and automation commands
└── README.md                         # Platform documentation and guide
```

---

## 5. Key Features

- **Explainable Risk Scoring:** Replaces opaque black-box probabilities with itemized signal cards (e.g. `KNOWN_SUSPICIOUS_IDENTIFIER` +20, `SHARED_INFRASTRUCTURE` +15, `RAPID_FUND_DISPERSION` +15) where signal points sum exactly to the final score.
- **Interactive Multi-Hop Fraud Graph:** Pan, zoom, node drag, 1/2/3-hop expansion, entity filtering, and real-time topology inspection.
- **Money-Flow Traversal:** Traces simulated fund dispersal from victim origin accounts across intermediary mules to final exit cash-out points. Flags fan-out and rapid layering automatically.
- **Coordinated Campaign Discovery:** Clusters incidents sharing malicious apex domains, collection UPI IDs, or VoIP sender numbers.
- **CYBER-ASSIST Grounded AI Investigator:** Grounded assistant answering *"Why was this flagged?"*, *"What connects these cases?"*, and *"What should I investigate next?"* with bracketed citations (`[CS-1024]`, `[DOMAIN-1]`, `[TX-9000]`).
- **Controlled Natural Language Search:** Translates natural queries into safe, parameterized database queries without arbitrary SQL generation.

---

## 6. Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Data Validation:** Pydantic v2
- **Relational Store:** SQLAlchemy ORM (SQLite default for zero-friction local execution; PostgreSQL for containerized deployments)
- **Graph Analytics:** NetworkX (in-memory synchronized engine with abstract `IGraphService` interface)
- **Data Science:** pandas, NumPy, scikit-learn
- **Testing:** pytest (20/20 passing tests including security checks)

### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS (Dark SOC / Cyber Intelligence Console theme)
- **Icons:** Lucide Icons
- **Visualization:** Interactive custom SVG graph viewer & multi-hop flow diagram

---

## 7. Getting Started & Local Setup

### Prerequisites
- Python 3.11+ (tested on Python 3.11 and 3.13; Docker image utilizes Python 3.11-slim)
- Node.js 18+ and npm 9+

---

### A. Quick Start: Local Development (Windows PowerShell)

```powershell
# 1. Clone repository & navigate to project
cd "d:\CYBERSCOPE 2"

# 2. Setup Backend Virtual Environment
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Seed Demo Scenario ("Operation Phantom KYC")
python scripts/seed_demo.py

# 4. Start FastAPI Backend Server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In a second PowerShell terminal:
```powershell
# 5. Setup & Start Frontend Console
cd "d:\CYBERSCOPE 2\frontend"
npm install
npm run dev
```

Open **`http://localhost:5173`** in your browser.  
FastAPI API Docs: **`http://localhost:8000/docs`**

---

### B. Quick Start: macOS / Linux

```bash
# Backend Setup
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_demo.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Frontend Setup
cd ../frontend
npm install
npm run dev
```

---

### C. Docker Compose

CYBERSCOPE includes production-ready Docker Compose orchestration. Database port 5432 remains internal to the container network to prevent external host credential exposure:

```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: Accessible internally on the bridge network (credentials managed via `.env`)

*Note: On container startup, the backend automatically seeds the database with the "Operation Phantom KYC" demo dataset if the table is empty.*

---

## 8. Demo Scenario: "Operation Phantom KYC"

CYBERSCOPE includes a pre-seeded, deterministic investigative scenario called **"Operation Phantom KYC"**:
- **5 Victims** receiving urgent bank account deactivation / KYC suspension SMS lures.
- **Shared Phishing Domain:** `secure-kyc-update.com`
- **Shared Central Collection UPI ID:** `centralmule99@okaxis`
- **Primary Mule Account:** `SIM-ACC-MULE-HUB-891`
- **Layering Beneficiaries:** 3 secondary accounts receiving fan-out disbursements within 4 minutes.

### 3-Minute Live Hackathon Demo Walkthrough

1. **Step 1 — Overview Dashboard:**
   - Open `http://localhost:5173`.
   - Show 42 total incidents, 7 high-risk cases, 2 critical syndicates, and 3 detected campaigns.
2. **Step 2 — Open Isolated Case:**
   - Click case **`CS-1024`** (*"Simulated KYC Suspension Alert - Victim Rajiv"*).
3. **Step 3 — Review Explainable Risk Score & Arithmetic:**
   - Notice the **`84/100 (HIGH)`** score with itemized signals that sum exactly to 84:
     - `KNOWN_SUSPICIOUS_IDENTIFIER` (+20 pts)
     - `SHARED_INFRASTRUCTURE` (+15 pts)
     - `MULTI_CASE_ASSOCIATION` (+15 pts)
     - `SUSPICIOUS_COMMUNICATION_PATTERN` (+15 pts)
     - `RAPID_FUND_DISPERSION` (+15 pts)
     - `UNUSUAL_AMOUNT` (+4 pts)
     - **Sum = 84 / 100** (Severity: HIGH `70–89`, CRITICAL `90–100`).
   - View the chronological timeline from initial SMS to the ₹48,500 outbound transfer.
4. **Step 4 — Expand Fraud Graph ("Find Connections"):**
   - Click **"Find Connections"** above the graph.
   - The graph expands from 1 hop to 2 hops, revealing domain `secure-kyc-update.com`.
   - Click again (3 hops) to reveal connected cases `CS-1025` and `CS-1026`, and collection UPI `centralmule99@okaxis`.
5. **Step 5 — Trace Funds:**
   - Click **"Trace Funds"** in the lower panel.
   - Observe the multi-hop visual tree showing the initial transfer, rapid fan-out across 3 secondary accounts, and forwarding to the exit node.
6. **Step 6 — Consult CYBER-ASSIST:**
   - Click **`Why was this case flagged?`** in the AI assistant.
   - Click **`What entities connect these cases?`** to view verified shared infrastructure.
   - Click **`What should an investigator examine next?`** for prioritized defensive actions.

---

## 9. Evaluation & Benchmark Results

CYBERSCOPE evaluates both internal deterministic regression integrity and real-world held-out performance with noise and evasive edge cases:

```powershell
python backend/scripts/evaluate_patterns.py
```

### Detection Metrics Comparison:
| Evaluation Scope | Precision | Recall | F1 Score | False Positive Rate | Purpose / Nature |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Deterministic Regression Check** | **100.00%** | **100.00%** | **1.0000** | **0.00%** | Internal regression check on 42 planted synthetic fixtures |
| **Held-Out Adversarial & Noisy Evaluation** | **72.73%** | **53.33%** | **0.6154** | **20.00%** | Real-world noisy test set with obfuscation & false-positive traps |

### Analytical Accuracy Metrics:
| Metric | Benchmark Result | Status |
| :--- | :--- | :--- |
| **Entity Resolution Accuracy** | **100.00%** | Tested on Phone/Domain/UPI normalizers |
| **Campaign Infrastructure Discovery** | **100.00%** | 5/5 shared hub entities identified |
| **Money-Flow Traversal & Fan-Out** | **100.00%** | Multi-hop BFS traversal & fan-out reconstruction |

*(Evaluation reflects honest heuristic performance on synthetic data).*

---

## 10. Running Tests & Security Self-Checks

```powershell
cd backend
pytest tests/ -v
```

**20 automated tests** verify:
- Phone, domain, URL, and UPI normalizations
- Regex extraction & **ReDoS resistance** (pathological strings parsed in < 50ms)
- Communication urgency, authority impersonation, and threat marker analysis
- Behavioral burst velocity, fan-out, and circular fund flow loops
- **XSS payload sanitization** (scam evidence script tags safely neutralized before storage)
- **Upload abuse prevention** (rejection of oversized payloads > 50KB with HTTP 413)
- Full REST API integration across all endpoints

---

## 11. Known Limitations

- **Uncalibrated Heuristic Weights:** Risk scoring weights (+20, +15, +4) are hand-picked expert priors rather than mathematically calibrated weights learned via empirical regression on live banking telemetry.
- **Synthetic Scope Only:** All accounts, phone numbers, and victim complaints are procedurally generated synthetic models; real-world data contains carrier noise, OCR scanning errors, and regional language variations.
- **No Authentication / Access Controls (RBAC):** As a hackathon prototype and research console, CYBERSCOPE assumes deployment inside a secure, authenticated network perimeter.
- **Offline Cash Conversions:** Money-flow tracing terminates at physical OTC cash withdrawals or ATM endpoints not recorded in digital telemetry.
- **Graph Scale & Interface Scope:** The active in-memory NetworkX implementation is optimized for fast local demonstrations and test suites. Neo4j is specified as an abstract interface design pattern (`IGraphService`) rather than an active distributed cluster.

---

## 12. Submission Details

- **Platform:** CYBERSCOPE
- **Version:** 1.0.0 (Hackathon MVP)
- **Status:** Complete, Tested (20/20 Passing Tests), and Documented.
