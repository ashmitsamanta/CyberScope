# CYBERSCOPE — Fraud Detection & Behavioral Analytics Methodology

## 1. Core Philosophy: The Evidence Chain
Cyber-enabled financial fraud rarely occurs as an isolated occurrence. Criminal operations rely on reused infrastructure to achieve economic scale:
1. Reused phishing domains and URL landing pages.
2. Reused SMS gateway phone senders.
3. Reused mule bank accounts and UPI payment handles.
4. Layered fund transfers to fragment balances below reporting limits.

CYBERSCOPE systematically correlates evidence across independent incident reports to reveal the underlying operational syndicate.

---

## 2. Behavioral & Anomaly Detection Heuristics

### 2.1 Velocity & Burst Analysis
- **Definition:** Quantifies the frequency of transactions occurring within tight temporal intervals (1 minute, 5 minutes, 15 minutes).
- **Rule:** If an account triggers $\ge 4$ transactions within a 15-minute window, the engine flags `RAPID_TRANSACTION_BURST` (+15 points).

### 2.2 Fan-Out & Fan-In Ratios
- **Fan-Out (One-to-Many):** A single aggregator account disperses funds across $\ge 3$ distinct beneficiaries within a 1-hour window. Flags `HIGH_FAN_OUT` (+15 points).
- **Fan-In (Many-to-One):** An account receives deposits from $\ge 3$ distinct originators within a 1-hour window. Flags `HIGH_FAN_IN` (+15 points).

### 2.3 Rapid Fund Dispersion (Mule Behavior)
- **Heuristic:** An inflow of $\ge ₹10,000$ is followed by outward transfers of $\ge 75\%$ of the received volume within 30 minutes across $\ge 2$ recipients.
- **Signal:** `RAPID_FUND_DISPERSION` (+20 points).

### 2.4 Dormancy-to-Burst Detection
- **Heuristic:** An account with zero transaction activity for $> 30$ days suddenly initiates high-velocity or high-value transfers.
- **Signal:** `DORMANCY_TO_BURST` (+15 points).

### 2.5 Circular Fund Flow Detection
- **Heuristic:** Traverses directed transfer edges to identify cycles of length $2 \le k \le 5$ ($A \to B \to C \to A$) intended to wash funds or simulate artificial transaction volume.
- **Signal:** `CIRCULAR_MOVEMENT` (+20 points).

---

## 3. Communication Content Analysis
Deterministic token & regex rules detect deceptive social engineering:
- **Authority Impersonation:** Regulators (RBI), law enforcement (Cyber Crime Cell, Police), utility boards, and financial institutions.
- **Coercive Urgency:** Deadlines under 2 hours, immediate deactivation threats.
- **Threat Markers:** Account blocking, SIM suspension, arrest warrants.
- **Credential Harvesting:** OTP, PIN, CVV, or remote screen sharing applications (AnyDesk, TeamViewer).

---

## 4. Graph Analytics & Shared Infrastructure
- **Shared Hubs:** Any infrastructure node (domain, phone, UPI, device) that intersects $\ge 2$ distinct cases is elevated to `SHARED_INFRASTRUCTURE` (+15 points).
- **Multi-Case Clustering:** Intersections across $\ge 3$ cases indicate an active coordinated campaign (`MULTI_CASE_ASSOCIATION`).
