# CYBERSCOPE — Complete Functions & Subsystems Reference Guide

This document provides a comprehensive technical index and explanation of all functions, classes, methods, API endpoints, analyzers, services, and frontend scripts implemented across the **CYBERSCOPE** codebase.

---

## 1. Architectural Summary & System Flow

CYBERSCOPE operates as an end-to-end cyber-fraud intelligence and investigation pipeline. Its data and functional flow is divided into 7 distinct stages:

```
[Raw Telemetry / Lures] 
       │
       ▼
1. INGESTION & EXTRACTION (app/utils/normalization.py, app/services/ingestion_service.py)
       │  - Deterministic linear regex extraction (Phones, Domains, URLs, UPIs, Amounts)
       │  - Entity normalization (E.164, URL stripping, UPI lowercase)
       ▼
2. ENTITY RESOLUTION & STORAGE (app/services/entity_service.py, app/models/)
       │  - Relational deduplication by (entity_type, normalized_value)
       │  - Relationship edge creation in SQLite / PostgreSQL
       ▼
3. FRAUD GRAPH SYNCHRONIZATION (app/services/graph_service.py, app/analyzers/graph_analyzer.py)
       │  - In-memory directed graph construction (NetworkX)
       │  - Neighborhood expansion (k-hops), shortest path, cycle detection (A->B->C->A)
       ▼
4. MULTI-LAYER BEHAVIORAL ANALYZERS (app/analyzers/)
       │  - CommunicationAnalyzer: Scam markers, authority impersonation, urgency
       │  - BehavioralAnalyzer: 15-min burst, fan-out/fan-in, dormancy-to-burst
       │  - TransactionAnalyzer: High-value transfers, micro-structuring (<₹50k)
       ▼
5. EXPLAINABLE RISK SCORING (app/services/risk_service.py)
       │  - Transparent itemized additive signals capped at 100 points
       │  - Explicit arithmetic breakdown (e.g. 20 + 15 + 15 + 15 + 15 + 4 = 84 PTS)
       ▼
6. MONEY-FLOW TRAVERSAL & CAMPAIGN CLUSTERING (app/services/transaction_service.py, campaign_service.py)
       │  - BFS traversal of fund dispersal across mule chains
       │  - Clustering cross-case shared infrastructure into campaigns
       ▼
7. GROUNDED AI INVESTIGATOR & UI CONSOLE (app/services/ai_service.py, frontend/)
          - Evidence-grounded CYBER-ASSIST & NVIDIA NIM LLM Proxy (/api/chat)
          - Multi-page Cyber-Neon interface with live telemetry & workspace
```

---

## 2. Backend Normalization & Utility Functions

Location: [`backend/app/utils/normalization.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/utils/normalization.py)

### `normalize_phone(phone: str) -> str`
- **Purpose**: Normalizes synthetic phone numbers into standard E.164-like format (`+91xxxxxxxxxx`).
- **Logic**: Strips whitespace, dashes, brackets, and periods. Evaluates leading `+91`, `91`, or `0`. If 10 digits remain, prepends `+91`.
- **Returns**: Formatted phone string or digits prefixed with `+`.

### `normalize_domain(domain_or_url: str) -> str`
- **Purpose**: Extracts and canonicalizes the hostname from an arbitrary URL or domain string.
- **Logic**: Adds a scheme prefix if absent, parses using `urllib.parse.urlparse`, removes port specifications, strips leading `www.`, and converts to lowercase. Includes a regex fallback for malformed strings.
- **Returns**: Clean domain name (e.g., `secure-kyc-update.com`).

### `normalize_url(url: str) -> str`
- **Purpose**: Normalizes a full URL to canonical form.
- **Logic**: Prepends `https://` if missing a scheme, lowercases the hostname, removes `www.`, strips trailing slashes, and preserves query parameters.
- **Returns**: Clean URL string.

### `normalize_upi(upi_id: str) -> str`
- **Purpose**: Canonicalizes UPI virtual payment addresses (`vpa@handle`).
- **Logic**: Converts string to lowercase and strips surrounding whitespace.
- **Returns**: Lowercased UPI ID (e.g., `centralmule99@okaxis`).

### `normalize_email(email: str) -> str`
- **Purpose**: Normalizes email addresses.
- **Logic**: Strips whitespace and converts all characters to lowercase.
- **Returns**: Clean email address string.

### `normalize_bank_account(account: str) -> str`
- **Purpose**: Normalizes bank account numbers or synthetic tokens.
- **Logic**: Strips whitespace, dashes, and periods; converts alphanumeric characters to uppercase.
- **Returns**: Uppercase account identifier (e.g., `AC-MULE-4482`).

### `normalize_entity_value(entity_type: str, value: str) -> str`
- **Purpose**: Universal dispatcher routing any entity value to its appropriate normalizer based on `entity_type`.
- **Supported Types**: `PHONE`, `DOMAIN`, `URL`, `UPI_ID`, `EMAIL`, `BANK_ACCOUNT`, `IP_ADDRESS`, `DEVICE`.
- **Returns**: Normalized value string.

### `EntityExtractor.extract_all(text: str) -> Dict[str, List[Any]]`
- **Purpose**: Deterministic linear regex entity extractor from unformatted text (SMS messages, emails, complaints).
- **Security**: Hardened against Regular Expression Denial of Service (ReDoS) by bounding input length to 50,000 characters and using non-overlapping linear segment patterns.
- **Extracted Fields**:
  - `phones`: Normalized `+91` numbers.
  - `domains`: Apex hostnames.
  - `urls`: Full web links.
  - `upi_ids`: Payment handles (filtering out standard email domains like `@gmail`, `@yahoo`).
  - `emails`: Valid email addresses.
  - `amounts`: Currency values parsed from ₹ / Rs / INR prefixes.
- **Returns**: Dictionary with lists of unique extracted and normalized entities.

---

## 3. Backend Analyzers

Location: [`backend/app/analyzers/`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/analyzers/)

### 3.1 Transaction Analyzer
Location: [`backend/app/analyzers/transaction_analyzer.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/analyzers/transaction_analyzer.py)

#### `TransactionAnalyzer.evaluate_transaction(transaction, sender_entity, receiver_entity, recent_sender_txs) -> Dict[str, Any]`
- **Purpose**: Evaluates an individual financial transaction and its immediate context for fraud indicators.
- **Signals Evaluated**:
  1. `LARGE_VALUE_TRANSFER` (+15 pts): Transfer volume $\ge ₹100,000$.
  2. `SIGNIFICANT_TRANSFER` (+8 pts): Transfer volume $\ge ₹45,000$.
  3. `HIGH_RISK_BENEFICIARY` (+25 pts): Receiver entity has existing risk score $\ge 60/100$.
  4. `HIGH_RISK_ORIGINATOR` (+20 pts): Sender entity has existing risk score $\ge 60/100$.
  5. `POTENTIAL_STRUCTURING` (+12 pts): Transaction amount between $₹48,000$ and $₹49,999$ (benchmarking the $₹50,000$ mandatory reporting threshold).
  6. `BURST_TRANSFER` (+15 pts): Sender performed $\ge 3$ transactions in a short window.
- **Returns**: Dictionary containing capped `risk_score` (0–100), `status` (`FLAGGED` or `SUCCESS`), `signals` list, and `is_flagged` boolean.

---

### 3.2 Graph Analyzer
Location: [`backend/app/analyzers/graph_analyzer.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/analyzers/graph_analyzer.py)

#### `GraphAnalyzer.__init__()`
- **Purpose**: Initializes the internal `networkx.DiGraph()` instance.

#### `GraphAnalyzer.build_from_records(entities, relationships, transactions=None) -> None`
- **Purpose**: Populates the in-memory directed graph from lists of entities (nodes), relationships (directed edges), and transactions (transfer edges).
- **Node Attributes**: `numeric_id`, `label`, `normalized_value`, `entity_type`, `risk_score`, `meta_data`.
- **Edge Attributes**: `relationship_type`, `confidence`, `amount`, `channel`, `timestamp`, `transaction_ref`.

#### `GraphAnalyzer.get_neighborhood(center_id: str, max_hops: int = 2, max_nodes: int = 150) -> Dict[str, Any]`
- **Purpose**: Extracts an investigative subgraph centered around a specific entity node up to `max_hops` depth.
- **Logic**: Converts graph to an undirected view, runs `nx.single_source_shortest_path_length`, limits to `max_nodes`, and returns the induced subgraph.
- **Returns**: Dictionary of `nodes` and `edges` with hop distances.

#### `GraphAnalyzer.find_shortest_path(source_id: str, target_id: str) -> Optional[List[Dict[str, Any]]]`
- **Purpose**: Finds the shortest investigative path between two entities regardless of edge directionality.
- **Returns**: List of node dictionaries representing the path, or `None` if disconnected.

#### `GraphAnalyzer.detect_circular_flows(max_cycle_length: int = 5) -> List[Dict[str, Any]]`
- **Purpose**: Detects directed cycles in money transfer edges ($A \to B \to C \to A$) commonly used for laundering or artificial volume generation.
- **Logic**: Filters edges to transfer types (`TRANSFERRED_TO`, `SENT`) and evaluates `nx.simple_cycles` for cycle lengths $2 \le k \le 5$.
- **Returns**: List of detected cycle structures with participant nodes and human-readable explanations.

#### `GraphAnalyzer.find_connected_components() -> List[List[str]]`
- **Purpose**: Identifies weakly connected clusters of entities to discover isolated attack syndicate groups.
- **Returns**: List of node ID lists sorted in descending order by cluster size.

#### `GraphAnalyzer.calculate_centrality_anomalies(top_k: int = 10) -> List[Dict[str, Any]]`
- **Purpose**: Identifies unusually high-connectivity entities (degree $\ge 4$) serving as operational nexus points or mule hubs.
- **Returns**: Sorted list of top centrality entities with explanations.

---

### 3.3 Communication Analyzer
Location: [`backend/app/analyzers/communication_analyzer.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/analyzers/communication_analyzer.py)

#### `CommunicationAnalyzer.analyze(content: str, url: str = None) -> Dict[str, Any]`
- **Purpose**: Deterministic rule-based inspection of communication text (SMS, emails, chat logs) for social engineering patterns without relying on stochastic LLMs.
- **Patterns Evaluated**:
  - `URGENCY`: Expiry warnings, immediate actions ("act now", "within 2 hours").
  - `IMPERSONATION`: Mimicking regulators (RBI), law enforcement (Cyber Cell, Police), banks (SBI, HDFC, ICICI), or utility departments.
  - `ACCOUNT_THREAT`: Account deactivation, SIM card blocking, arrest warrant threats.
  - `VERIFICATION_SCAM`: KYC expiry, Aadhaar/PAN linking lures.
  - `CREDENTIAL_REQUEST`: Demands for OTP, PIN, password, or remote screen-sharing tools (AnyDesk, TeamViewer, RustDesk).
  - `PAYMENT_REQUEST`: Processing fees, refundable security deposits.
  - `LOTTERY_REFUND_BAIT`: Fake cashbacks, lottery prizes, unclaimed refunds.
  - `SUSPICIOUS_LINK`: Suspicious TLD extensions (`.xyz`, `.top`, `.icu`, `.buzz`, etc.).
  - `TYPOSQUATTING_LINK`: Domain mimics recognized brands without matching their legitimate domains.
- **Returns**: Dictionary with `suspicion_score` (capped at 100), `categories`, `is_suspicious` boolean, and itemized `findings`.

---

### 3.4 Behavioral Analyzer
Location: [`backend/app/analyzers/behavioral_analyzer.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/analyzers/behavioral_analyzer.py)

#### `BehavioralAnalyzer.analyze_account_transactions(account_id: int, transactions: List[Dict[str, Any]], reference_time: Optional[datetime] = None) -> Dict[str, Any]`
- **Purpose**: Analyzes the historical financial ledger of an account to identify anomalous fraud behaviors.
- **Rules Evaluated**:
  1. `RAPID_TRANSACTION_BURST` (+15 pts): $\ge 4$ transactions within a 15-minute window.
  2. `HIGH_FAN_OUT` (+15 pts): Distributing funds to $\ge 3$ distinct beneficiaries within 1 hour.
  3. `HIGH_FAN_IN` (+15 pts): Receiving deposits from $\ge 3$ distinct senders within 1 hour.
  4. `RAPID_FUND_DISPERSION` (+20 pts): Mule behavior where incoming funds of $\ge ₹10,000$ are followed by outward transfers of $\ge 75\%$ of the volume within 30 minutes across $\ge 2$ recipients.
  5. `DORMANCY_TO_BURST` (+15 pts): Account dormant for $\ge 30$ days suddenly executes rapid high-velocity transfers.
  6. `UNUSUAL_AMOUNT` (+10 pts): Latest transaction amount is $> 3.5\times$ historical median and exceeds $₹15,000$.
- **Returns**: Dictionary with `behavior_risk_score`, `signals`, `patterns_detected`, and transaction counts.

---

## 4. Backend Services

Location: [`backend/app/services/`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/)

### 4.1 Entity Service
Location: [`backend/app/services/entity_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/entity_service.py)

#### `EntityService.get_or_create(db: Session, entity_type: str, value: str, risk_score: float = 0.0, metadata: Optional[Dict[str, Any]] = None, timestamp: Optional[datetime] = None) -> Tuple[Entity, bool]`
- **Purpose**: Persists or updates entities with deterministic deduplication by `(entity_type, normalized_value)`. Updates `last_seen` timestamp and merges metadata if existing.
- **Returns**: `(Entity, was_created)` tuple.

#### `EntityService.create_relationship(db: Session, source_id: int, target_id: int, relationship_type: str, confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None, timestamp: Optional[datetime] = None) -> Relationship`
- **Purpose**: Creates or updates a directed graph edge between two entities. Updates `last_seen` timestamp if edge already exists.
- **Returns**: The created or existing `Relationship` ORM instance.

#### `EntityService.get_entity_neighbors(db: Session, entity_id: int) -> List[Dict[str, Any]]`
- **Purpose**: Retrieves all direct incoming and outgoing relational neighbors for a given entity.
- **Returns**: List of connected entity dictionaries including relationship type, confidence, and direction.

#### `EntityService.find_connected_cases(db: Session, entity_id: int) -> List[Dict[str, Any]]`
- **Purpose**: Discovers all investigation cases linked to an entity through graph relationships.
- **Returns**: List of connected case summaries.

---

### 4.2 Graph Service
Location: [`backend/app/services/graph_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/graph_service.py)

#### `NetworkXGraphService.sync_from_db(db: Session, force: bool = False) -> None`
- **Purpose**: Synchronizes the in-memory NetworkX directed graph with all entity, relationship, and transaction records from the relational database. Skips if already synced unless `force=True`.

#### `NetworkXGraphService.resolve_entity(db: Session, entity_identifier: Any) -> Optional[Entity]`
- **Purpose**: Flexible entity resolver supporting integer IDs (`1`), node IDs (`e-1`), or normalized entity values (e.g. phone `+919686579303`, domain `secure-kyc-update.com`, UPI, URL).

#### `NetworkXGraphService.get_full_graph(db: Session, limit: int = 150) -> Dict[str, Any]`
- **Purpose**: Retrieves the global graph up to `limit` nodes and their connecting edges. Enriches nodes with `degree`, `connected_case_count`, and `connected_cases` in `metadata`.

#### `NetworkXGraphService.get_case_graph(db: Session, case_identifier: Any, hops: int = 2) -> Dict[str, Any]`
- **Purpose**: Extracts an investigative subgraph anchored on a specific case. Supports either integer ID (`1`) or case number string (`CS-1024`, `CS-1027`). Enriches nodes with degree and connected cases, and returns comprehensive case `stats`.

#### `NetworkXGraphService.get_neighborhood(db: Session, entity_identifier: Any, hops: int = 2) -> Dict[str, Any]`
- **Purpose**: Retrieves the neighborhood subgraph centered on a specific entity ID or normalized identifier up to $k$-hops depth.

#### `NetworkXGraphService.find_shortest_path(db: Session, source_id: int, target_id: int) -> Optional[List[Dict[str, Any]]]`
- **Purpose**: Computes the shortest investigative path between two entities in the synced graph.

#### `NetworkXGraphService.detect_circular_flows(db: Session) -> List[Dict[str, Any]]`
- **Purpose**: Traces circular financial flows ($A \to B \to C \to A$) in the synced graph.

#### `NetworkXGraphService.find_shared_infrastructure(db: Session) -> List[Dict[str, Any]]`
- **Purpose**: Identifies digital infrastructure entities (`PHONE`, `DOMAIN`, `UPI_ID`, `DEVICE`, `IP_ADDRESS`) that intersect 2 or more distinct cases within 2 hops.
- **Returns**: Sorted list of shared infrastructure items with connected case counts and case identifiers.

---

### 4.3 Risk Service
Location: [`backend/app/services/risk_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/risk_service.py)

#### `RiskEngine.evaluate_case(db: Session, case_id: int) -> Dict[str, Any]`
- **Purpose**: Computes the transparent, explainable investigation risk score for a case.
- **Design Philosophy**: Strict arithmetic addition capped at 100 points, avoiding black-box opacity.
- **Signals Evaluated**:
  1. `KNOWN_SUSPICIOUS_IDENTIFIER` (+20 pts): Entity with prior risk score $\ge 70$.
  2. `SHARED_INFRASTRUCTURE` (+15 pts): Linked identifier recurs across $\ge 2$ cases.
  3. `MULTI_CASE_ASSOCIATION` (+15 pts): Linked identifier recurs across $\ge 3$ cases.
  4. `SUSPICIOUS_COMMUNICATION_PATTERN` (+15 pts): Scam language markers detected in communications.
  5. `RAPID_FUND_DISPERSION` (+15 pts): Mule dispersal of stolen funds.
  6. `RAPID_TRANSACTION_BURST` (+15 pts): High transaction frequency in case window ($\ge 8$ transfers).
  7. `UNUSUAL_AMOUNT` (+4 to +10 pts): Stolen volume exceeds exposure thresholds.
  8. `BASELINE_MONITORING`: Applied if no explicit signals trigger.
- **Severity Bands**:
  - `LOW`: 0–39 points (Routine / ambient noise)
  - `MEDIUM`: 40–69 points (Analyst review required)
  - `HIGH`: 70–89 points (Active multi-vector investigation)
  - `CRITICAL`: 90–100 points (Confirmed syndicate; immediate escalation)
- **Returns**: Dictionary with exact arithmetic `score`, `level`, itemized `signals` list, `thresholds`, and human-readable `summary`.

---

### 4.4 Transaction & Fund Trace Service
Location: [`backend/app/services/transaction_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/transaction_service.py)

#### `TransactionService.trace_funds(db: Session, start_entity_id: Optional[int] = None, start_transaction_id: Optional[int] = None, max_hops: int = 4, time_window_hours: int = 72, min_amount: float = 0.0) -> Dict[str, Any]`
- **Purpose**: Executes a Breadth-First Search (BFS) graph traversal tracing outbound fund movements from a victim account or initial fraudulent transaction.
- **Node Classification**: Categorizes accounts along the path into roles: `SOURCE`, `MULE` (hop 1), `INTERMEDIARY` (intermediate hops), `DESTINATION` (terminal hop).
- **Flow Anomalies Detected**:
  - `FAN_OUT`: Account dispersing funds to $\ge 3$ beneficiaries at a hop.
  - `RAPID_LAYERING`: Fund movement traversing $\ge 3$ sequential hops.
  - `CIRCULAR_MOVEMENT`: Funds looping back to a previously visited account node.
- **Returns**: Traversed tree with `total_volume_traced`, `nodes`, `edges`, `detected_patterns`, and flow summary.

---

### 4.5 Campaign Service
Location: [`backend/app/services/campaign_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/campaign_service.py)

#### `CampaignService.detect_and_sync_campaigns(db: Session) -> List[Dict[str, Any]]`
- **Purpose**: Scans the fraud graph for shared infrastructure clusters and updates campaign case and entity metrics.
- **Returns**: List of active coordinated campaigns.

#### `CampaignService.get_campaign_detail(db: Session, campaign_id_or_code: str) -> Optional[Dict[str, Any]]`
- **Purpose**: Retrieves full dossier on a campaign, including linked incident cases, shared indicator assets, and chronological operational milestones.

---

### 4.6 Timeline Service
Location: [`backend/app/services/timeline_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/timeline_service.py)

#### `TimelineService.get_case_timeline(db: Session, case_id: int) -> List[Dict[str, Any]]`
- **Purpose**: Constructs a unified chronological evidence stream for an investigation case by aggregating:
  1. `CASE_INITIALIZED`: Initial complaint filing.
  2. `COMMUNICATION_RECEIVED`: Ingestion of phishing SMS, spoofed calls, or emails.
  3. `INDICATOR_FLAGGED`: System detection of threat markers.
  4. `FINANCIAL_TRANSACTION`: Stolen transfers and mule movement events.
- **Returns**: Chronologically sorted list of timeline events.

---

### 4.7 Ingestion Service
Location: [`backend/app/services/ingestion_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/ingestion_service.py)

#### `IngestionService.ingest_report(db: Session, title: str, content: str, channel: str = "SMS", sender_phone: Optional[str] = None, source: str = "SYNTHETIC_FEED") -> Dict[str, Any]`
- **Purpose**: End-to-end ingestion pipeline processing unformatted complaint text or SMS messages.
- **Execution Steps**:
  1. Generates unique case number (`CS-xxxx`).
  2. Extracts entities using `EntityExtractor.extract_all`.
  3. Analyzes message language using `CommunicationAnalyzer.analyze`.
  4. Persists `Case`, `CASE` entity, and extracted `PHONE`, `DOMAIN`, `URL`, `UPI_ID` entities.
  5. Creates `REPORTED_IN` relationships linking entities to the case.
  6. Stores communication record in `Message` table.
  7. Logs detected scam indicators in `Indicator` table.
  8. Evaluates explainable risk score using `RiskEngine.evaluate_case`.
  9. Triggers graph re-synchronization (`graph_service.sync_from_db(db, force=True)`).
- **Returns**: Ingested case summary, extracted entities, and risk evaluation.

---

### 4.8 AI Intelligence Service (CYBER-ASSIST)
Location: [`backend/app/services/ai_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/ai_service.py)

#### `DeterministicExpertProvider.generate_response(query: str, context: Dict[str, Any]) -> Dict[str, Any]`
- **Purpose**: Default offline, evidence-grounded expert investigator. Generates structured, citation-backed analyses (`[CASE-xxx]`, `[DOMAIN-xxx]`, `[TX-xxx]`) without hallucinations or external API dependencies.
- **Intent Handlers**:
  - `Risk / Flagged`: Explains why a case was flagged with exact signal point breakdowns.
  - `Connections / Shared`: Explains shared infrastructure and multi-hop links.
  - `Money Flow / Funds`: Details fund volume, mule layers, and flow anomalies.
  - `Recommendations / Next Steps`: Outlines strategic defensive actions (freezes, takedowns, SAR alerts).
- **Response Structure**: Strictly separates **Observed Evidence**, **Calculated Signals**, **Inferences**, **Uncertainties**, and **Recommended Next Steps**.

#### `OpenAIProvider.generate_response(query: str, context: Dict[str, Any]) -> Dict[str, Any]`
- **Purpose**: LLM provider for OpenAI-compatible APIs using strict grounding prompts. Falls back to `DeterministicExpertProvider` on network failure or missing API key.

#### `AIService.answer_query(db: Session, query: str, case_id: Optional[int] = None) -> Dict[str, Any]`
- **Purpose**: Orchestrator assembling relational context (case details, risk signals, linked entities, transactions, timeline, fund trace) and dispatching to the configured AI provider.

---

### 4.9 Authentication & Identity Service
Location: [`backend/app/services/auth_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/auth_service.py)

#### `SupabaseAuthService.is_configured() -> bool`
- **Purpose**: Checks whether `SUPABASE_URL` and `SUPABASE_ANON_KEY` are defined.

#### `SupabaseAuthService.extract_token_from_header(request: Request) -> Optional[str]`
- **Purpose**: Extracts the Bearer token string from the HTTP `Authorization` request header.

### 4.9 Authentication, User Database & Verification Service
Location: [`backend/app/services/auth_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/auth_service.py) & [`backend/app/models/user.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/models/user.py)

#### `User` Model (`users` table)
- **Fields**: `id`, `email` (unique, lowercase), `password_hash` (PBKDF2-HMAC-SHA256), `name`, `phone` (E.164), `role`, `organization`, `is_verified_email`, `is_verified_phone`, `is_active`, `created_at`, `updated_at`.
- **Method `to_dict()`**: Safely serializes investigator identity claims while strictly redacting password hashes.

#### `UserVerification` Model (`user_verifications` table)
- **Fields**: `id`, `email`, `phone`, `name`, `password_hash`, `role`, `organization`, `email_otp` (6-digit), `sms_otp` (6-digit), `expires_at` (10-minute window), `created_at`, `attempts`.

#### `hash_password(password: str) -> str`
- **Purpose**: Generates PBKDF2-HMAC-SHA256 password hash using 100,000 iterations and a 16-byte cryptographically secure random salt (`secrets.token_hex`).

#### `verify_password(password: str, hashed: str) -> bool`
- **Purpose**: Constant-time verification of raw password against hashed value via `hmac.compare_digest`.

#### `create_access_token(user_dict: dict, expires_delta=...) -> str`
- **Purpose**: Generates signed HS256 JWT access tokens encoded with investigator identity attributes (`sub`, `email`, `name`, `role`, `organization`).

#### `SupabaseAuthService.is_configured() -> bool`
- **Purpose**: Checks whether `SUPABASE_URL` and `SUPABASE_ANON_KEY` are defined.

#### `SupabaseAuthService.extract_token_from_header(request: Request) -> Optional[str]`
- **Purpose**: Extracts the Bearer token string from the HTTP `Authorization` request header.

#### `SupabaseAuthService.verify_token(token: str) -> Dict[str, Any]`
- **Purpose**: Verifies JWT access tokens across multiple fallback tiers:
  1. Pre-configured demo tokens (`demo-token`, `demo-session-token`) $\to$ returns demo investigator profile.
  2. Local backend PBKDF2 / HS256 JWT decoding and validation.
  3. HMAC-SHA256 signature verification using `SUPABASE_JWT_SECRET`.
  4. Supabase REST Auth API verification (`GET {SUPABASE_URL}/auth/v1/user`).
  5. Local unverified claim decoding for development flexibility.

#### `SupabaseAuthService.get_current_user(request: Request) -> Dict[str, Any]`
- **Purpose**: FastAPI dependency for route authentication. If `REQUIRE_AUTH=False` and no header is provided, safely returns `DEMO_USER`.

---

## 5. Backend REST API Endpoints

Location: [`backend/app/api/`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/api/)

| Method | Endpoint | Handler Function | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | `health_check` | Service readiness, active graph engine, and defensive scope disclaimer |
| `GET` | `/api/stats/dashboard` | `get_dashboard_stats` | SOC dashboard KPIs, risk distribution, top campaigns, and high-risk case queue |
| `GET` | `/api/cases` | `list_cases` | Filter cases by status, severity, minimum risk score, or text search |
| `GET` | `/api/cases/{case_id}` | `get_case` | Comprehensive case detail with itemized risk signal breakdown |
| `GET` | `/api/cases/{case_id}/timeline` | `get_case_timeline` | Unified chronological evidence timeline |
| `POST` | `/api/cases/ingest` | `ingest_new_case_report` | Ingests raw scam complaint, extracts entities, and creates graph edges |
| `PATCH`| `/api/cases/{case_id}` | `update_case` | Updates case status, severity, title, or metadata |
| `GET` | `/api/entities` | `list_entities` | Search and filter digital identifiers (phones, domains, UPIs, accounts) |
| `GET` | `/api/entities/{entity_id}` | `get_entity` | 360-degree entity dossier with connected cases and relationships |
| `GET` | `/api/entities/{entity_id}/neighbors` | `get_entity_neighbors` | Direct incoming and outgoing relational neighbors |
| `GET` | `/api/graph` | `get_fraud_graph` | Global network graph nodes and edges with type/search/risk filtering |
| `GET` | `/api/graph/case/{case_identifier}` | `get_case_subgraph` | Subgraph localized around a specific case (supports numeric ID or `CS-xxxx`) |
| `GET` | `/api/graph/entity/{entity_identifier}` | `get_entity_neighborhood` | $k$-hop expansion around an entity (supports ID or normalized string) |
| `GET` | `/api/graph/shortest-path` | `find_shortest_path` | Shortest path between two entity nodes |
| `GET` | `/api/graph/circular-flows` | `detect_circular_flows` | Directed transaction cycles ($A \to B \to C \to A$) |
| `GET` | `/api/graph/shared-infrastructure` | `get_shared_infrastructure` | Infrastructure nodes linked to $\ge 2$ distinct cases |
| `GET` | `/api/transactions` | `list_transactions` | Financial ledger with counterparty values, amounts, channels, and flags |
| `GET` | `/api/transactions/{tx_id}` | `get_transaction` | Single transaction detail |
| `POST`| `/api/transactions/trace-funds` | `trace_money_flow` | BFS multi-hop fund traversal from an account or initial fraudulent transfer |
| `GET` | `/api/campaigns` | `list_campaigns` | Active coordinated fraud campaigns and cluster statistics |
| `GET` | `/api/campaigns/{campaign_id_or_code}` | `get_campaign` | Campaign detail with shared indicators and connected cases |
| `POST`| `/api/investigations/query` | `query_cyber_assist` | Grounded AI query answering with citations and calculated signals |
| `POST`| `/api/investigations/summary` | `generate_case_summary` | Generates executive investigation brief for a case |
| `GET` | `/api/investigations/case/{case_id}` | `get_case_investigation_logs` | Historical CYBER-ASSIST query logs for a case |
| `GET` | `/api/search` | `natural_language_search` | Controlled intent-based search parser translating queries into database filters |
| `POST`| `/api/chat` & `/api/chat/completions` | `chat_proxy` | Zero-CORS proxy to NVIDIA NIM (`meta/llama-3.2-11b-vision-instruct`) with local fallback |
| `POST`| `/api/auth/check-email` | `check_email_availability` | Real-time validation checking if email already exists in database |
| `POST`| `/api/auth/register/initiate` | `initiate_registration` | Validates new user, checks duplicates (409), and generates dual Email/SMS OTPs |
| `POST`| `/api/auth/register/verify` | `verify_registration_otp` | Validates dual OTPs, commits new User to database, and issues access token |
| `POST`| `/api/auth/register/resend` | `resend_registration_otp` | Regenerates verification codes with 30s rate-limit cooldown |
| `POST`| `/api/auth/login` | `login_user` | Authenticates database investigator with PBKDF2 password verification |
| `GET` | `/api/auth/config` | `get_auth_config` | Public Supabase client configuration and demo account credentials |
| `GET` | `/api/auth/me` | `get_authenticated_user` | Current authenticated investigator profile from access token |
| `POST`| `/api/auth/verify` | `verify_access_token` | Validates access token and returns investigator profile |

---

## 6. Backend Lifecycle & Scripts

### 6.1 Application Entrypoint & Lifecycle
Location: [`backend/app/main.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/main.py)

- `lifespan(app: FastAPI)`: Async context manager executed on startup and shutdown. Manages database connection retry loops (up to 10 attempts for container readiness), table schema creation, automatic demo data seeding if database is empty, and Fraud Graph memory synchronization.
- `global_exception_handler(request, exc)`: Centralized exception handler preventing unhandled 500 error leaks.
- `root()`: Root landing route returning service descriptor and documentation links.

### 6.2 Database Session Management
Location: [`backend/app/database.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/database.py)

- `get_db()`: Generator yielding an isolated SQLAlchemy database session with automatic closure on request completion. Configured with `check_same_thread: False` for SQLite and connection pooling (`pool_pre_ping=True`).

### 6.3 Automation Scripts
Location: [`backend/scripts/`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/scripts/)

- `seed_database(db_session=None, drop_existing=True)` ([`seed_demo.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/scripts/seed_demo.py)): Seeds the database with the pre-configured "Operation Phantom KYC" scenario (42 cases, 2 critical cases, 7 high-risk cases, 3 campaigns, connected entities, transactions, and messages).
- `generate_synthetic_dataset(profile="demo", num_accounts=100, num_transactions=300)` ([`generate_dataset.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/scripts/generate_dataset.py)): Generates a deterministic synthetic dataset with fixed seed 42, creating multi-case clusters, shared domains, mule chains, and SMS lures with zero real-world PII.
- `evaluate_synthetic_benchmarks()` ([`evaluate_patterns.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/scripts/evaluate_patterns.py)): Runs precision, recall, and F1 evaluation across both planted deterministic fixtures (100% precision/recall) and 30 held-out noisy adversarial cases (72.7% precision, 53.3% recall).
- `reset_demo.py`: One-command utility to wipe and re-seed the demonstration environment.

---

## 7. Frontend Architecture & Client-Side Functions

Location: [`frontend/`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/frontend/)

CYBERSCOPE features a **Multi-Page Application (MPA)** architecture styled with a custom Cyber-Neon glassmorphism design system (`Inter` and `Space Grotesk` fonts, CSS variables, micro-animations, glowing status indicators).

### 7.1 Shared Application Shell (`cyberscope.js`)
Location: [`frontend/assets/cyberscope.js`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/frontend/assets/cyberscope.js)

- `cyberscopeUser()`: Retrieves the current user profile from `window.CyberScopeAuth` or `localStorage.getItem('cyberscopeUser')`.
- `cyberscopeInitials(name)`: Generates two-letter uppercase avatar initials (e.g., "Special Agent" $\to$ "SA").
- `cyberscopeProtect()`: Route guard executed by internal pages. Verifies active session token; if invalid or missing, redirects to `signin.html?redirect=...`. Synchronizes profile name, avatar, and role in the top navigation bar.
- `signOut()`: Clears active tokens and session state, calling `CyberScopeAuth.signOut()` and redirecting to `signin.html`.
- `cyberscopeSetActiveNav()`: Detects the current page filename from `window.location.pathname` and applies the `.active` CSS class to the matching navigation link.
- `cyberscopeInitNav()`: Initializes mobile drawer navigation with backdrop toggle and Escape key listener.
- `cyberscopeAnswer(question)`: Local keyword-based fallback response engine providing instant definitions of Fraud Graph, Cases, Entities, Transactions, Campaigns, and Workspace when the backend AI is offline.
- `cyberscopeInitChat()`: Initializes the floating CyberScope Assistant drawer. Manages chat opening/closing, user input, animated typing indicator, `/api/chat` backend requests with bearer tokens, and automatic fallback to `cyberscopeAnswer`.

---

### 7.2 Supabase Authentication Client (`supabase-client.js`)
Location: [`frontend/assets/supabase-client.js`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/frontend/assets/supabase-client.js)

- `loadScript(src)`: Dynamically loads the `@supabase/supabase-js` v2 library from CDN if not already present.
- `fetchServerConfig()`: Queries `GET /api/auth/config` to dynamically discover Supabase project credentials.
- `init()`: Asynchronously initializes the Supabase client using configured or server-provided credentials, setting up auth state listeners (`onAuthStateChange`) to persist sessions and tokens to `localStorage`.
- `getUser()`: Returns cached investigator user object.
- `isAuthenticated()`: Returns boolean indicating whether an active authenticated session exists.
- `getAuthHeaders()`: Generates HTTP headers containing `{ "Authorization": "Bearer <access_token>" }` for authenticated backend API requests.
- `signIn(credentials)`: Authenticates investigator via Supabase `signInWithPassword` or validates pre-seeded demo account (`investigator@cyberscope.io` / `password123`).
- `signUp(data)`: Registers a new investigator with metadata (name, phone, role, organization) via Supabase `signUp` or creates a local evaluation user.
- `signOut()`: Signs out from Supabase and purges cached tokens from `localStorage`.
- `resetPassword(email)`: Dispatches password reset instructions via Supabase Auth.
- `verifySession()`: Validates current session token against Supabase `getSession()`.
- `setCustomConfig(url, key)` / `clearCustomConfig()`: Allows runtime in-browser configuration of custom Supabase project credentials.

---

### 7.3 Page-Level Modules & Scripts

#### A. Showcase Landing Page (`CyberScope.html` / `index.html`)
- `scrollToSection(id)`: Smoothly scrolls viewport to designated section.
- `showDemo()` / `closeDemo()`: Opens and closes interactive demo modal with background scroll lock.
- `toggleChat()`: Opens floating AI intelligence drawer.
- `sendMessage()`: Submits user query to `/api/chat` proxy with streaming typing indicator and local keyword fallback.
- `quickQuestion(question)`: Pre-populates and fires recommended question chips.
- `syncLivePlatformStats()`: Queries `GET /api/stats/dashboard` on load and updates live case, entity, and campaign counters.

#### B. Operations Dashboard (`dashboard.html`)
- `dashboardRequireAuth()`: Displays an inline authentication gate modal if unauthenticated instead of a hard redirect.
- `dashboardLoadUser()`: Loads user greeting and investigator details into the overview header.
- `syncLiveDashboardData()`: Fetches live stats from `/api/stats/dashboard` and populates the recent high-risk cases queue (`/api/cases?limit=3`).

#### C. Case Registry (`cases.html`)
- `filterCases()`: Real-time client-side search filtering table rows by keyword or case ID.
- `loadLiveCases()`: Fetches live cases from `/api/cases` and renders table with severity tags (`HIGH`, `MEDIUM`, `LOW`).
- `createNewCase()`: Interactive intake modal taking case title and scam lure text, sending to `POST /api/cases/ingest` and refreshing the table upon completion.

#### D. Fraud Graph Explorer (`fraud-graph.html`)
- Interactive Cyber-Neon fraud network explorer powered by Cytoscape.js (`v3.28.1`) with full backend integration.
- `initCytoscape()`: Instantiates the Cytoscape graph canvas with customized Cyber-Neon styles (hexagons for cases, ellipses for phones, round-rectangles for domains, diamonds for UPIs, rectangles for bank accounts; glowing high-risk borders; directed curved edges with amount and relationship labels).
- `formatNodeForCy(n)` & `formatEdgeForCy(e)`: Transforms backend graph JSON schema into Cytoscape data elements with risk badges, labels, and topology classes.
- `renderGraphElements(graphData)`: Clears canvas and populates with new nodes and edges, updating HUD metrics and entity filter badges.
- `updateCountsHUD(nodeCount, edgeCount)`: Refreshes visible node and edge counts in the HUD header.
- `updateEntityFilterCounts(nodes)`: Calculates item counts across entity types (Cases, Domains, Phones, UPI IDs, Accounts, High Risk).
- `getLayoutConfig(name)` & `applyLayout(name, animate)`: Configures and triggers Cytoscape layouts (`cose` force-directed, `concentric`, `circle`, `breadthfirst`, `grid`).
- `zoomIn()`, `zoomOut()`, `fitView()`, `resetGraphView()`: Canvas viewport navigation controls.
- `setEntityFilter(type)`: Filters visible elements on canvas by entity type or high-risk status.
- `handleSearchInput(val)` & `executeSearch()`: Real-time search highlighting matching nodes, dimming others, and centering the viewport.
- `inspectNode(node)`: Opens the Node Inspector side panel displaying detailed forensic dossier (label, type, risk badge, progress meter, degree, connected cases, metadata) and actionable navigation buttons.
- `highlightNeighborhood(node)`: Highlights 1-hop connected neighbors of a selected node and dims unrelated elements.
- `expandCurrentEntity(hops)`: Queries `GET /api/graph/entity/{numeric_id}?hops=N` and dynamically merges new nodes and edges into the active Cytoscape canvas without re-centering.
- `mergeElementsIntoCy(graphData)`: Seamlessly unions new graph elements into existing canvas with incremental layout.
- `fetchSharedInfrastructure()` & `focusSharedInfraItem(idx)`: Discovers nexus infrastructure entities linking $\ge 2$ cases (`GET /api/graph/shared-infrastructure`) and highlights them with amber/cyan pulses.
- `fetchCircularFlows()` & `animateCycle(idx)`: Detects directed transaction loops (`GET /api/graph/circular-flows`) and executes sequential red edge pulsation.
- `runShortestPath()` & `renderPathResult(data)`: Calculates shortest investigative path between two entities via `GET /api/graph/shortest-path` and highlights the step-by-step breadcrumb trail.
- `loadCasesDropdown()` & `handleCaseChange(caseVal)`: Populates case selector from `GET /api/cases` and loads selected case subgraphs via `GET /api/graph/case/{caseId}`.
- `loadFullGraph()`: Fetches global graph overview via `GET /api/graph?limit=150`.
- `processUrlParameters()`: Parses `?case_id=`, `?case_number=`, `?entity_id=`, and `?search=` to automatically load and focus on target subgraphs upon entry from other pages.

#### E. Digital Entity Directory (`entity-explorer.html`)
- `filterEntities()`: Client-side table search filtering entities by type, value, or risk score.
- `loadLiveEntities()`: Fetches entities from `/api/entities` and renders identifier dossiers with degree connectivity and risk badges.

#### F. Financial Ledger Explorer (`transaction-explorer.html`)
- `loadLiveTransactions()`: Queries `GET /api/transactions` and populates financial ledger with transaction reference, sender, receiver, formatted amount (`₹`), and `FLAGGED` / `NORMAL` status tags.

#### G. Coordinated Campaign Explorer (`campaign-explorer.html`)
- Visualizes clustered syndicates (e.g., *Utility-Bill Cluster*, *KYC Phishing Network*, *Impersonation Cluster*).
- Displays shared infrastructure metrics (domains, phones, UPI IDs) and operational timeline milestones.

#### H. Investigation Workspace (`investigation-workspace.html`)
- `saveNotes()`: Saves investigator scratchpad observations directly to `localStorage` with a temporary saved indicator.
- `loadCaseDetail()`: Reads `?case_id=` from the URL, queries `GET /api/cases/{case_id}`, and populates workspace metrics, risk score cards, and entity counts.

#### I. Authentication & Identity Verification (`signin.html`, `register.html`, `backend/app/models/user.py`, `backend/app/api/auth.py`, `backend/app/services/notification_service.py`)
- **Database Models** ([`backend/app/models/user.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/models/user.py)):
  - `User`: Primary user database record (`users` table). Normalizes lowercase email, stores PBKDF2-HMAC-SHA256 password hash, E.164 phone (`+91...`), verification status flags (`is_verified_email`, `is_verified_phone`), role, organization, and timestamp audits. Includes safe `to_dict()` masking sensitive credentials.
  - `UserVerification`: Pending registration staging record (`user_verifications` table). Stores 6-digit `email_otp`, 6-digit `sms_otp`, 10-minute expiry timestamp, registration metadata, and verification attempt counter.
- **Cryptographic Services & Utilities** ([`backend/app/services/auth_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/auth_service.py)):
  - `hash_password(password)`: Generates salt-backed PBKDF2-HMAC-SHA256 hash using 100,000 iterations.
  - `verify_password(password, hashed)`: Constant-time hash verification via `hmac.compare_digest`.
  - `create_access_token(user_dict, expires_delta)`: Issues cryptographically signed HS256 JWT access tokens containing investigator identity claims and metadata.
- **Production Notification & Real Dispatch Service** ([`backend/app/services/notification_service.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/services/notification_service.py)):
  - `EmailDispatcher.send_verification_email(to_email, recipient_name, code)`: Dispatches real MIME multipart emails via standard SMTP (`smtplib`) with TLS/SSL support, styled with CyberScope's cyber-neon theme, security badge, 6-digit monospace code box, and plain-text fallback.
  - `SmsDispatcher.send_verification_sms(to_phone, code)`: Dispatches real SMS text messages across multiple providers:
    - **Twilio**: REST API dispatch via HTTP Basic Auth.
    - **Fast2SMS**: Direct OTP route for Indian mobile carrier networks.
    - **Custom Webhook**: Enterprise SMS gateway proxy dispatch.
  - `NotificationService.get_test_outbox()` / `clear_test_outbox()`: In-memory capture for automated testing environments without leaking secrets to HTTP clients or UI.
- **Authentication Endpoints** ([`backend/app/api/auth.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/backend/app/api/auth.py)):
  - `POST /api/auth/check-email`: Fast non-blocking lookup returning whether an email exists in the database.
  - `POST /api/auth/register/initiate`: Validates input formatting; returns HTTP 409 `ACCOUNT_EXISTS` if email is already taken. For new users, generates dual 6-digit cryptographically secure OTPs, stages pending verification in `user_verifications`, dispatches real email via SMTP and SMS messages via SMS carrier gateway (`notification_service`), and returns delivery status without leaking OTP codes in API responses.
  - `POST /api/auth/register/verify`: Validates dual OTP codes against pending verification using constant-time `hmac.compare_digest`. Enforces brute-force lockout (purges record and locks out after 5 failed attempts with HTTP 429). Upon success, commits verified `User` to database and returns signed JWT access token.
  - `POST /api/auth/register/resend`: Regenerates fresh OTP codes with active 60-second rate-limiting cooldown (HTTP 429), and dispatches fresh codes via email and SMS.
  - `POST /api/auth/login`: Authenticates registered database users with password verification; returns HTTP 404 `USER_NOT_FOUND` if account doesn't exist, HTTP 401 `INVALID_PASSWORD` if credentials fail, or HTTP 200 with JWT access token upon successful authentication.
- **Production Two-Step Onboarding UI** ([`frontend/register.html`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/frontend/register.html)):
  - **Step 1 (Account Details)**: Real-time 400ms debounced duplicate email check calling `/api/auth/check-email` with inline warning alert and "Sign in instead" link; form submission calling `/api/auth/register/initiate` with smooth GPU transition to Step 2.
  - **Step 2 (Real Dual Verification Screen)**:
    - **Masked Contact Displays**: Shows `s***a@example.com` and `+91 98*** **210`.
    - **Zero-Exposure Policy**: OTP security codes are never rendered in DOM elements or browser responses, ensuring true out-of-band 2FA verification.
    - **Real Carrier & SMTP Dispatch Indicators**: Displays real-time delivery status for SMTP and cellular gateways. When SMTP or SMS credentials in `.env` are unconfigured or fail, provides transparent diagnostic feedback so administrators can populate `.env`.
    - **Dedicated 6-Digit Monospace Inputs**: Formatted input boxes with paste handlers that strip spaces and auto-advance focus.
    - **60-Second Live Resend Timer**: Displays `Resend codes in 59s...` with live dispatch feedback.
    - **Direct Database Commit**: Verifies identity, inserts `User` record into database, sets local session, and redirects to `dashboard.html`.
- **Integrated Sign-In Screen** ([`frontend/signin.html`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/frontend/signin.html)):
  - Reads URL search parameter `?email=...` to pre-populate input when redirected from duplicate registration warnings.
  - Authenticates against database via `POST /api/auth/login`, provides clear 404 guidance linking directly to registration, and falls back to offline demo credentials (`investigator@cyberscope.io` / `password123`) if network is absent.
- **Client Auth Helper** ([`frontend/assets/supabase-client.js`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/frontend/assets/supabase-client.js)):
  - Coordinates `checkEmail()`, `verifyRegistration()`, `resendVerification()`, `signIn()`, and `signUp()` with backend database endpoints.



---

### 7.4 Standalone Python Server & Reverse Proxy (`frontend/server.py`)
Location: [`frontend/server.py`](file:///home/sambuddhapal/Documents/GNIT%20Hackathon/Code/CyberScope/frontend/server.py)

- `load_env()`: Traverses directory tree to discover and load variables from `.env` into `os.environ`.
- `CyberScopeHandler.end_headers()`: Injects permissive CORS headers (`Access-Control-Allow-Origin: *`, `Methods`, `Headers`).
- `CyberScopeHandler._proxy_to_backend(method)`: Reverse-proxies all `/api/...` endpoints (GET, POST, OPTIONS) to the FastAPI backend running on port 8000.
- `CyberScopeHandler.do_GET()`: Serves static frontend assets, intercepts `/api/auth/config`, and proxies all other `/api/` calls.
- `CyberScopeHandler.do_POST()`: Intercepts `/api/chat` for NVIDIA NIM LLM completion, and proxies all other `/api/` calls (including `/api/auth/...`) to FastAPI.
- `run_server(port=8000)`: Boots HTTP server on designated port, falling back to 8080/8888 if the port is in use.

---

## 8. Summary Table of Key Classes & Interfaces

| Component | Class / Interface | Key Responsibility |
| :--- | :--- | :--- |
| Normalization | `EntityExtractor` | Linear regex extraction of digital identifiers with ReDoS protection |
| Analyzer | `TransactionAnalyzer` | Evaluates amount structuring, velocity bursts, and counterparty risks |
| Analyzer | `GraphAnalyzer` | NetworkX topological analysis, $k$-hop expansion, and circular flows |
| Analyzer | `CommunicationAnalyzer`| Rule-based detection of urgency, authority impersonation, and phishing lures |
| Analyzer | `BehavioralAnalyzer` | Detects fan-out, fan-in, rapid mule dispersion, and dormancy-to-burst |
| Service | `EntityService` | Deterministic deduplication, persistence, and relational indexing |
| Service | `IGraphService` | Abstract interface for graph database and topology operations |
| Service | `NetworkXGraphService` | In-memory graph engine synchronized with relational database |
| Service | `RiskEngine` | Transparent explainable risk scoring (0–100) with additive signals |
| Service | `TransactionService` | BFS recursive money-flow fund traversal across mule chains |
| Service | `CampaignService` | Cross-incident clustering using shared infrastructure |
| Service | `TimelineService` | Unified chronological evidence sequencing |
| Service | `IngestionService` | End-to-end evidence ingestion and graph link creation |
| Service | `IAIProvider` | Abstract interface for evidence-grounded AI investigators |
| Service | `DeterministicExpertProvider` | Hallucination-free, citation-grounded AI intelligence engine |
| Service | `OpenAIProvider` | OpenAI/NVIDIA LLM provider with grounding system prompt |
| Service | `SupabaseAuthService` | JWT authentication and session verification |
| Client Auth | `CyberScopeAuth` | Frontend Supabase authentication and session persistence |
