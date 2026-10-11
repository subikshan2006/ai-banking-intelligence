# AI Banking Intelligence & Autonomous Multi-Agent Platform

A production-inspired enterprise banking intelligence platform featuring an autonomous multi-agent architecture that models simulated real-time core banking, ML fraud detection, cryptographic approval workflows, policy RAG, and role-based access. It runs fully deployable in the cloud (Render + Vercel) **or** as a standalone self-contained Windows EXE.

Live demo:

- Frontend: `https://banking-ai-frontend-three.vercel.app`
- Backend API: `https://banking-ai-backend-wez9.onrender.com` (Swagger docs at `/docs`)

---

## 🏛️ Architecture & System Design

The application directly reflects the **9-Layer Banking AI Reference Architecture**:

```
 🌐 Layer 1: Client Interfaces & Dashboards (React 18/19, Vite, TypeScript, Tailwind CSS)
 🔌 Layer 2: API Gateway & WebSocket Router (FastAPI, Lifespan Manager, CORS, Correlation IDs)
 🧠 Layer 3: Intent Router & Orchestrator (Regex/Pattern Classifier + Supervisor Agent + LLM Planner)
 🤖 Layer 4: Specialist Multi-Agent Core (Customer, Transaction, Fraud, Credit, Compliance, Investigation)
 🛠️ Layer 5: Tool & Integration Layer (Customer Data, Account Ops, ML Fraud Model, Policy RAG)
 🛡️ Layer 6: Security, Compliance & Governance (JWT Auth, RBAC, Cryptographic Approvals, Audit Logs)
 📚 Layer 7: Enterprise Knowledge RAG (TF-IDF Policy Vector Retriever, Versioned Specs)
 ⚡ Layer 8: Transaction Simulator & Async Pipeline (FastAPI Lifespan Task, WebSockets)
 💾 Layer 9: Database & Persistence Layer (SQLite WAL Mode, Thread-Isolated Task Sessions)
```

### High-Level Approach

The platform models how a real bank's **AI operations layer** would sit on top of
simulated core-banking systems: every capability is implemented as a **tool** exposed
through a registry, and every tool is invoked by one or more **agents** that are
orchestrated by a **supervisor**. Nothing in the demo mutates a real ledger except the
explicit, human-verified state-changing tools gated behind an approval workflow.

#### End-to-End Request Lifecycle

```
User NL query → Authentication (JWT)
  → 1. INTENT CLASSIFICATION    SupervisorAgent maps the query to a known intent + entities
  → 2. PLANNING                SupervisorAgent builds a task DAG (LLM-proposed, then validated,
                               or deterministic fallback) with dependency ordering
  → 3. AGENT EXECUTION         Specialized agents resolve their tasks via the Tool Registry
  → 4. AGGREGATION             SupervisorAgent merges tool outputs into a structured snapshot
  → 5. ANSWER SYNTHESIS        LLM writes a grounded, Markdown answer using only tool data;
                               every step is written to the append-only audit trail
```

Key design decisions:

- **LLM planning with validation, not blind trust.** When a Gemini key is configured,
  the Supervisor asks the model for a workflow plan. The returned JSON is validated
  against an allowlist of `{agent: action}` pairs, task IDs are checked for uniqueness,
  and dependencies must form a valid order. Any violation falls back to the
  deterministic planner (`plan_source` is recorded in the trace).
- **Deterministic by default.** With no API key, the intent classifier and a rule-based
  planner execute the entire pipeline locally with zero external dependencies.
- **Grounding before generation.** The LLM only ever synthesizes answers from the
  `structured_data` produced by real tool calls (never raw model knowledge), keeping
  responses honest and auditable.

#### Agents and the Tool Registry

- The **Tool Registry** (`app/tools/registry.py`) is a declarative map of 21 simulated
  banking capabilities: customer 360 profiles, account operations, transaction
  analytics, rule + ML fraud scoring, loan/EMI/DTI calculators, policy RAG search, and
  the approval-request action (for state-changing work).
- **Wiring is code-gen friendly**: `*_tools.py` modules annotate functions with
  `@registry.register(...)` at import time, so new bank APIs become new tools
  (and automatically appear on the simulation, docs, and agent allowlists) without
  touching the orchestrator.

#### Human-in-the-Loop Approvals (Security Layer)

State-changing operations never execute autonomously:

```
Agent → request_simulated_approval() → Approval Queue (PENDING, 24h expiry)
  → Human reviewer (authenticated via JWT) inspects SHA-256 payload hash + rationale
  → Role permission matrix check (e.g. risk_analyst cannot approve FREEZE_ACCOUNT)
  → APPROVED → execute_action_by_type() mutates the simulated ledgers
  → REJECTED / EXPIRED → recorded, nothing executed
```

The acting role is always taken from the **JWT token** — never from the request body —
and every decision (including permission denials and expiry sweeps) is audited.

#### Security & Compliance

- **JWT authentication** (HS256, 12h expiry) with seeded roles:
  `manager` / `risk_analyst` / `compliance_officer`.
- **Integrity** is modeled via SHA-256 payload hashing and idempotency keys to
  prevent duplicate or tampered approvals.
- **Append-only audit log** with automatic regex-based PII masking (cards, emails,
  PANs, phones) so raw sensitive values never persist.

#### Knowledge RAG

Policy documents are chunked and indexed by a TF-IDF vector retriever; agent calls like
`search_policy` return the most relevant passages so the Compliance Agent answers with
versioned, citeable policy.

#### Real-Time Simulation

A lifespan-managed background task generates realistic transaction events (normal
spends, velocity bursts, duplicate charges, failed debits, high-value transfers) that
(a) feed the ML anomaly model, (b) create fraud alerts, and (c) stream over a WebSocket
to the dashboard in real time.

#### Data & Persistence

SQLite in WAL mode with a request-scoped session dependency, thread-isolated task
sessions for background agents, and a single `banking_demo.db` seeded with 15
customers, 25 accounts, 130+ transactions, fraud alerts, loans, policies, approvals,
and audit records. Cross-thread writes use short, retry-able commits.

---

## ✨ Key Features

1. **Autonomous Multi-Agent Core & LLM Intelligence**:
   - **Supervisor Agent**: Classifies intent, validates LLM-proposed task DAGs against agent/tool allowlists, then dispatches to specialized agents. Final answers are synthesized by an LLM (Google Gemini) grounded in tool results, with deterministic fallback when no API key is configured or the network is unavailable.
   - **Customer Agent**: Queries account profiles, balances, and multi-month spending behavior.
   - **Transaction Agent**: Extracts transaction histories, aggregates categories, and detects high-velocity spending.
   - **Fraud Agent**: Hybrid engine combining deterministic threshold rules with `IsolationForest` anomaly scoring.
   - **Credit Agent**: Computes EMI schedules, Debt-to-Income (DTI) ratios, and loan eligibility.
   - **Compliance Agent**: Conducts KYC status verification and policy checks.
   - **Investigation Agent**: Synthesizes cross-domain dossiers.
   - **Notification Agent**: Handles multi-channel alerts and real-time event broadcasts.

2. **Role-Based Access Control (JWT)**:
   - Separate logins for `manager`, `risk_analyst`, and `compliance_officer` with server-enforced permission boundaries.
   - Approve/reject endpoints require a valid JWT; the acting role is taken from the token (never the request body) and cross-checked against the action permission matrix.
   - Demo credentials:

   | Username           | Password          | Role                    | Permissions                                             |
   |--------------------|-------------------|-------------------------|---------------------------------------------------------|
   | `manager`          | `Manager@123`     | Branch Manager          | Full approval authority, all actions                    |
   | `risk_analyst`     | `Risk@123`        | Risk Analyst            | Read / monitoring only (no state-changing approvals)     |
   | `compliance_officer` | `Compliance@123` | Compliance Officer     | Freezes, unfreezes, policy exceptions                   |

3. **Explainable Hybrid Fraud Detection**:
   - Explicit separation between rule-based policy triggers (velocity bursts, duplicate transfers, rapid location jumps) and scikit-learn `IsolationForest` unsupervised ML anomaly scores.
   - Granular risk factor breakdowns for every transaction analysis.

4. **Cryptographic Approval & Governance Gateway**:
   - Critical operations (account freezes, large transfers, loan overrides, policy exceptions) trigger human-in-the-loop approval workflows.
   - Approvals require SHA-256 payload verification (`payload_hash = sha256(payload)`), strict single-use idempotency keys, and **24h expiry auto-enforcement** (`410` + `EXPIRED` on stale requests).

5. **Append-Only Auditing & PII Protection**:
   - Every login, agent execution, tool call, and decision is logged to an immutable audit trail.
   - Automatic regex-based PII sanitization masks credit card numbers (`****-****-****-1234`), emails (`u***@domain.com`), tax IDs, and phones.

6. **Real-Time Transaction Simulator**:
   - Background event engine producing realistic transaction streams with a live WebSocket feed (`ws://<host>/ws/simulator`).

7. **Automated Evaluation & Benchmark Suite**:
   - Run `python -m pytest` in `backend/` — 49 passing tests covering agents, approvals (expiry, tampering, RBAC), auth, LLM wiring, concurrency, and the 11 business use cases.

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- (Optional) A Google Gemini API key to enable live LLM answers.

### Configuration
Copy `backend/.env.example` to `backend/.env` and fill in values:

```env
LLM_PROVIDER=google
LLM_MODEL=gemini-3.8-flash
LLM_API_KEY=your-google-gemini-api-key-here
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
JWT_SECRET=replace-with-a-long-random-string
```

Leave `LLM_API_KEY` blank to run the deterministic fallback mode.

### Manual Launch

#### Backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation: `http://localhost:8000/docs`

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 📦 Standalone Windows EXE

A self-contained desktop build (backend + frontend + SQLite + ML model bundled in a single PyInstaller executable) is available:

1. Double-click `NexusBankingAI-Desktop.exe` (or run `NexusBankingAI-Setup.exe` to install it).
2. The whole platform opens **inside its own desktop window** (WebView2/Edge) — no browser tab, no visible server.
3. Sign in with the demo accounts above.

Requires Windows 10/11 (the embedded window uses the built-in Microsoft Edge WebView2 runtime).

Build from source (run from `backend/`):

```bash
pip install -r requirements.txt pyinstaller pywebview
pyinstaller --noconfirm --clean --onefile --windowed --name NexusBankingAIPlatform \
  --add-data "app;app" \
  --add-data ".env;." \
  --collect-all webview \
  --exclude-module pandas --exclude-module matplotlib \
  standalone_main.py
```

`standalone_main.py` starts the FastAPI service on `127.0.0.1:8765` and launches the
bundled `app/standalone_web` (`npm run build` output) in a desktop `webview` window.
Closing the window stops the platform.

---

## ☁️ Cloud Deployment Guide

### Deploying to Render (Backend)
1. Connect the GitHub repository to [Render](https://render.com) as a web service (`rootDir: backend`, `startCommand: uvicorn app.main:app ...`).
2. Set environment variables: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL`, `JWT_SECRET`, `FRONTEND_ORIGIN`.

### Deploying the Frontend to Vercel
1. Import the repository's `frontend/` directory as a Vite project.
2. Add `VITE_API_BASE_URL` → full URL of the deployed Render backend.

### Docker Compose
```bash
docker compose up --build -d
```
- **Frontend**: `http://localhost`
- **Backend API Docs**: `http://localhost:8000/docs`

To shut down:
```bash
docker compose down
```

---

## 🧪 Automated Benchmark Results

| Scenario ID | Category     | Description                          | Status |
|-------------|--------------|--------------------------------------|--------|
| CASE-01     | Customer     | Account balance inquiry               | PASSED |
| CASE-02     | Customer     | Transaction history query             | PASSED |
| CASE-03     | Customer     | Monthly spending summary             | PASSED |
| CASE-04     | Fraud        | Suspicious activity analysis          | PASSED |
| CASE-05     | Fraud        | Explain flagged transaction           | PASSED |
| CASE-06     | Credit       | Loan eligibility evaluation           | PASSED |
| CASE-07     | Credit       | Compare EMI scenarios                 | PASSED |
| CASE-08     | Credit       | Pending loan applications             | PASSED |
| CASE-09     | Compliance   | KYC status verification               | PASSED |
| CASE-10     | Policy       | Policy search RAG query               | PASSED |
| CASE-11     | Investigation | Cross-agent dossier build            | PASSED |

---

## 📄 License & System Status

Operational enterprise banking intelligence system. All bank data is synthetic and simulated; the LLM layer uses Google Gemini with an automatic deterministic fallback for offline operation.