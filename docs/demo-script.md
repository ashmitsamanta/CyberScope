# CYBERSCOPE — Hackathon Demo Script: "Operation Phantom KYC"

⏱️ **Target Duration:** ~3 Minutes

---

## Step 1: Open Intelligence Overview
1. Start at the main **Overview Dashboard**.
2. **Key Talking Point for Judges:**
   > "Welcome to CYBERSCOPE. Traditional fraud detection examines events in isolation, like a single complaint or transaction. CYBERSCOPE treats fraud as an interconnected evidence chain. Notice our platform telemetry: 42 total incidents, 7 high-risk cases, 2 critical syndicates, and 3 active detected campaigns."
3. Highlight the **Risk Spectrum** and **Coordinated Fraud Campaigns** cards.

---

## Step 2: Open an Apparently Isolated Case
1. Click on case **`CS-1024`** (*"Simulated KYC Suspension Alert - Victim Rajiv"*).
2. This immediately loads the flagship **Investigation Workspace**.

---

## Step 3: Explain the Risk Breakdown
1. Direct attention to the **Investigation Risk Score** badge: **`84/100 (HIGH)`**.
2. **Key Talking Point:**
   > "Notice this score is not a black-box percentage. Looking at the right panel, every single point is explainable: +20 points for a Known Suspicious Identifier, +15 points for Shared Infrastructure, and +15 points for Suspicious Communication Urgency."
3. Toggle the **Timeline** tab to show the chronological sequence from the initial SMS to the ₹48,500 transfer.

---

## Step 4: Expand the Fraud Graph ("Find Connections")
1. Click the **"Find Connections"** button in the header (or above the graph).
2. **Key Talking Point:**
   > "Watch what happens when the investigator clicks 'Find Connections'. The graph expands from 1 hop to 2 hops. Suddenly, this isolated victim is connected to a phishing domain: `secure-kyc-update.com`."
3. Click **"Find Connections"** again (3-Hops).
4. **Key Talking Point:**
   > "Expanding one more hop reveals the full syndicate: cases CS-1025 and CS-1026, telephone senders, and the central collection UPI ID `centralmule99@okaxis`."

---

## Step 5: Trace the Money Flow
1. Scroll down to the bottom left **"Simulated Money-Flow Trace"** panel.
2. Click **"Trace Funds"**.
3. **Key Talking Point:**
   > "Here is our graph traversal engine in action. Victim Rajiv transferred ₹48,500 to the Primary Mule Hub. Within 4 minutes, the hub executed a Fan-Out split across three secondary accounts, and forwarded onward to an exit node. Layering and Fan-out anomalies are flagged automatically."

---

## Step 6: Inquire with CYBER-ASSIST (AI Investigator)
1. Turn to the bottom right **CYBER-ASSIST** terminal.
2. Click the quick prompt: **`Why was this case flagged?`**
   - The AI returns an evidence-grounded response citing `[CASE-1024]`, `[DOMAIN-1]`, and itemizing observed signals.
3. Click the prompt: **`What entities connect these cases?`**
   - The AI identifies the shared domain and collection UPI handle.
4. Click: **`What should an investigator examine next?`**
   - The AI delivers concrete, strategic defensive steps (account freezing, registrar takedowns, payment gateway velocity limits).

---

## Step 7: Conclusion
1. **Closing Statement:**
   > "In less than 3 minutes, CYBERSCOPE transformed an isolated victim SMS into an uncovered multi-case syndicate, fully traced the money movement, and provided structured, non-hallucinatory evidence ready for defensive action."
