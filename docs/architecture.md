# CYBERSCOPE — Architecture & Technical Design

## 1. System Overview
CYBERSCOPE is an explainable cyber-fraud intelligence and investigation platform engineered for defensive security analysts, fraud investigators, and financial institutions. Its primary goal is not to prove criminal guilt, but to connect fragmented evidence, score risk transparently, trace simulated money movements, detect coordinated campaigns, and assist human investigators via grounded AI.

```
Synthetic Telemetry
       ↓
Data Ingestion (Regex & Pattern Parsers)
       ↓
Entity Extraction & Normalization
       ↓
Relationship Construction
       ↓
In-Memory Fraud Graph (NetworkX / Neo4j)
       ↓
Behavioral & Anomaly Engine
       ↓
Campaign Detection & Clustering
       ↓
Money-Flow Traversal Engine (BFS)
       ↓
Case Chronological Timeline
       ↓
Explainable Grounded AI (CYBER-ASSIST)
       ↓
Analyst Console (React + Vite + Tailwind)
```

---

## 2. Core Subsystems

### 2.1 Entity Extraction & Normalization
- **Extractors:** Deterministic regex extractors identify phone numbers (+91 synthetic numbers), domains, URLs, UPI handles (`id@bank`), bank account tokens, and currency amounts.
- **Normalizers:** Ensures strings like `+91 90000 00001`, `9000000001`, and `+919000000001` resolve to the exact same synthetic entity `+919000000001`. Domain normalizers strip schemes, `www.`, ports, and trailing paths.

### 2.2 Relational & Graph Storage
- **Relational Layer:** SQLAlchemy ORM managing SQLite for local frictionless execution and PostgreSQL for containerized deployments.
- **Graph Service Interface (`IGraphService`):**
  - Default: `NetworkXGraphService` builds an in-memory directed graph synchronized with the relational store.
  - Neo4j Bridge: Pluggable for large distributed graph databases via Cypher queries.
- **Algorithms:** $k$-hop neighborhood expansion, shortest path discovery, directed cycle detection (circular fund movements), weakly connected components, and degree centrality anomaly detection.

### 2.3 Explainable Risk Engine
- Capped at 100 points, avoiding misleading "probabilities".
- Transparent point breakdown with itemized signal codes:
  - `KNOWN_SUSPICIOUS_IDENTIFIER` (+20 pts)
  - `SHARED_INFRASTRUCTURE` (+15 pts)
  - `RAPID_TRANSACTION_BURST` (+15 pts)
  - `RAPID_FUND_DISPERSION` (+15 pts)
  - `MULTI_CASE_ASSOCIATION` (+15 pts)
  - `UNUSUAL_AMOUNT` (+10 pts)
  - `SUSPICIOUS_COMMUNICATION_PATTERN` (+10 pts)
- Severity classifications: LOW (<40), MEDIUM (40-69), HIGH (70-89), CRITICAL (90+).

### 2.4 Money-Flow Trace Engine
- BFS graph traversal from starting victim or fraudulent transaction.
- Classifies nodes into roles: `SOURCE`, `MULE`, `INTERMEDIARY`, `DESTINATION`.
- Flags behavioral patterns: `FAN_OUT` (one account distributing to $\ge 3$ recipients), `RAPID_LAYERING` ($\ge 3$ sequential hops), and `CIRCULAR_MOVEMENT` ($A \to B \to C \to A$).

### 2.5 CYBER-ASSIST (Grounded AI Investigator)
- Implements `AIProvider` abstraction.
- Default: `DeterministicExpertProvider` produces verifiable, citation-backed analyses (`[CASE-1024]`, `[DOMAIN-1]`, `[TX-9000]`) with zero hallucination risk and zero requirement for external API keys.
- Optional: `OpenAIProvider` passes structured context JSON to OpenAI-compatible LLMs under strict grounding system prompts.
- Explicitly separates: **Observed Evidence**, **Calculated Signals**, **Inferences**, and **Uncertainties**.
