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
- Powers an evidence-grounded AI assistant (**CYBER-ASSIST**) that provides actionable investigative answers without hallucinations.

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
      │          In-Memory Fraud Graph (NetworkX / Neo4j)      │
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

## 4. Key Features

- **Explainable Risk Scoring:** Replaces opaque black-box probabilities with itemized signal cards (e.g. `KNOWN_SUSPICIOUS_IDENTIFIER` +20, `SHARED_INFRASTRUCTURE` +15, `RAPID_TRANSACTION_BURST` +15).
- **Interactive Multi-Hop Fraud Graph:** Pan, zoom, node drag, 1/2/3-hop expansion, entity filtering, and real-time topology inspection.
- **Money-Flow Traversal:** Traces stolen fund dispersal from victim origin accounts across intermediary mules to final exit cash-out points. Flags fan-out and rapid layering automatically.
- **Coordinated Campaign Discovery:** Clusters incidents sharing malicious apex domains, collection UPI IDs, or VoIP sender numbers.
- **CYBER-ASSIST AI Investigator:** Grounded assistant answering *"Why was this flagged?"*, *"What connects these cases?"*, and *"What should I investigate next?"* with bracketed citations (`[CASE-1024]`, `[DOMAIN-1]`, `[TX-9000]`).
- **Controlled Natural Language Search:** Translates natural queries into safe, parameterized database queries without arbitrary SQL generation.

---

## 5. Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Data Validation:** Pydantic v2
- **Relational Store:** SQLAlchemy ORM (SQLite default for zero-friction local execution; PostgreSQL supported)
- **Graph Analytics:** NetworkX (in-memory synchronized engine with abstract `IGraphService` interface for Neo4j)
- **Data Science:** pandas, NumPy, scikit-learn
- **Testing:** pytest (17/17 passing tests)

### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS (Dark SOC / Cyber Intelligence Console theme)
- **Icons:** Lucide Icons
- **Visualization:** Interactive custom SVG/Canvas graph viewer & multi-hop flow diagram

---

## 6. Getting Started & Local Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
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

```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## 7. Demo Scenario: "Operation Phantom KYC"

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
3. **Step 3 — Review Explainable Risk Score:**
   - Notice the **`84/100 (HIGH)`** score with itemized signals: `KNOWN_SUSPICIOUS_IDENTIFIER` (+20), `SHARED_INFRASTRUCTURE` (+15), and `SUSPICIOUS_COMMUNICATION_PATTERN` (+15).
   - View the chronological timeline from initial SMS to the ₹48,500 outbound transfer.
4. **Step 4 — Expand Fraud Graph:**
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

## 8. Evaluation & Benchmark Results

Because the synthetic dataset contains known planted fraud patterns, an evaluation script tests detection precision, recall, and accuracy:

```powershell
python backend/scripts/evaluate_patterns.py
```

### Benchmark Results on Synthetic Ground Truth:
| Metric | Benchmark Result | Status |
| :--- | :--- | :--- |
| **High-Risk Case Detection Precision** | **100.00%** | Verified |
| **High-Risk Case Detection Recall** | **100.00%** | Verified |
| **Planted Pattern F1-Score** | **1.0000** | Verified |
| **False Positive Rate (FPR)** | **0.00%** | Verified |
| **Entity Resolution Accuracy** | **100.00%** | Verified |
| **Campaign Infrastructure Detection** | **100.00%** | Verified |
| **Money-Flow Graph Traversal** | **100.00%** | Verified |

*(Evaluation performed on deterministic synthetic benchmark data).*

---

## 9. Running Tests

```powershell
cd backend
pytest tests/ -v
```

17 automated tests verify phone/domain/UPI normalizations, regex extraction, communication analysis, behavioral burst velocity, circular fund flow loops, and all REST endpoints.

---

## 10. Known Limitations

- **Synthetic Scope:** All phone numbers, bank accounts, and people are fictional simulations; real-world data contains OCR artifacts and carrier noise.
- **Offline Cash Conversions:** Money-flow tracing stops at physical OTC cash withdrawals or ATM endpoints not recorded in ledger telemetry.
- **Graph Scale:** The default in-memory NetworkX implementation is optimized for fast local demonstrations up to ~100,000 nodes. For planetary-scale deployments, connect the Neo4j backend via `GRAPH_BACKEND=neo4j`.

---

## 11. Team & Hackathon Submission

Built for the Hackathon by a senior engineering and security architecture team.
- **Platform:** CYBERSCOPE
- **Version:** 1.0.0 (Hackathon MVP)
- **Status:** Complete, Tested, and Verified Locally.
