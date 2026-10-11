# AI Banking Intelligence & Autonomous Multi-Agent Platform

A production-inspired, fully local, standalone enterprise banking intelligence platform featuring an autonomous multi-agent architecture built to model simulated real-time core banking, ML fraud detection, cryptographic approval workflows, and policy RAG intelligence.

---

## 🏛️ Architecture & System Design

The application directly reflects the **9-Layer Banking AI Reference Architecture**:

```
 🌐 Layer 1: Client Interfaces & Dashboards (React 18/19, Vite, TypeScript, Tailwind CSS)
 🔌 Layer 2: API Gateway & WebSocket Router (FastAPI, Lifespan Manager, CORS, Correlation IDs)
 🧠 Layer 3: Intent Router & Orchestrator (Regex/Pattern Classifier + Supervisor Agent)
 🤖 Layer 4: Specialist Multi-Agent Core (Customer, Transaction, Fraud, Credit, Compliance, Investigation)
 🛠️ Layer 5: Tool & Integration Layer (Customer Data, Account Ops, ML Fraud Model, Policy RAG)
 🛡️ Layer 6: Security, Compliance & Governance (Cryptographic Approvals, PII Masking, Audit Logs)
 📚 Layer 7: Enterprise Knowledge RAG (TF-IDF Policy Vector Retriever, Versioned Specs)
 ⚡ Layer 8: Transaction Simulator & Async Pipeline (FastAPI Lifespan Task, WebSockets)
 💾 Layer 9: Database & Persistence Layer (SQLite WAL Mode, Thread-Isolated Task Sessions)
```

---

## ✨ Key Features

1. **Autonomous Multi-Agent Core**:
   - **Supervisor Agent**: Plans and dispatches DAG tasks to specialized agents based on user intent.
   - **Customer Agent**: Queries account profiles, balances, and multi-month spending behavior.
   - **Transaction Agent**: Extracts transaction histories, aggregates categories, and detects high-velocity spending.
   - **Fraud Agent**: Hybrid engine combining deterministic threshold rules with `IsolationForest` anomaly scoring.
   - **Credit Agent**: Computes EMI schedules, Debt-to-Income (DTI) ratios, and loan eligibility.
   - **Compliance Agent**: Conducts KYC status verification and policy checks.
   - **Investigation Agent**: Synthesizes cross-domain customer, transaction, fraud, and credit profiles into comprehensive case dossiers.
   - **Notification Agent**: Handles multi-channel alerts and real-time event broadcasts.

2. **Explainable Hybrid Fraud Detection**:
   - Explicit separation between rule-based policy triggers (e.g., velocity bursts, duplicate transfers, rapid location jumps) and scikit-learn `IsolationForest` unsupervised ML anomaly scores.
   - Generates granular risk factor breakdowns for every transaction analysis.

3. **Cryptographic Approval & Governance Gateway**:
   - Critical operations (e.g., high-risk account freezes, large loan approvals > ₹2,00,000) trigger human-in-the-loop approval workflows.
   - Approvals require SHA-256 payload verification (`payload_hash = sha256(payload)`) and strict token single-use idempotency.

4. **Append-Only Auditing & PII Protection**:
   - Every agent execution, tool call, and policy check is logged to an immutable audit trail.
   - Automatic regex-based PII sanitization masks credit card numbers (`****-****-****-1234`), emails (`u***@domain.com`), and tax IDs (`PAN: *****1234F`).

5. **Real-Time Transaction Simulator**:
   - Background event engine producing realistic transaction streams (normal purchases, sudden spikes, duplicate transfers, rapid location jumps, and failed payments).
   - Live WebSocket feed (`ws://localhost:8000/ws/simulator`) pushing events to the UI header banner in real-time.

6. **Automated Evaluation & Benchmark Suite**:
   - Includes an automated benchmark evaluation runner (`scripts/run_evaluations.py`) testing intent classification accuracy, agent task completion, and execution latency across 11 standard test scenarios (achieves 100% pass rate).

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 1-Click Launch (Windows)
Double-click `start.bat` in the root directory. This script will automatically:
1. Initialize SQLite WAL mode database (`banking.db`) and pre-train the ML model.
2. Start the FastAPI backend server on `http://localhost:8000`.
3. Launch the Vite React frontend on `http://localhost:5173`.
4. Open your default web browser to the dashboard.

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

## 🛠️ CLI Utilities

### Reset Database & Seed Baseline Data:
```bash
python scripts/reset_demo.py
```

### Run Automated Benchmark Evaluation Suite:
```bash
python scripts/run_evaluations.py
```

---

## 🧪 Automated Benchmark Results

| Scenario ID | Category | Description | Status | Latency |
|-------------|----------|-------------|--------|---------|
| CASE-01 | Customer | Account balance inquiry | PASSED | 35ms |
| CASE-02 | Customer | Transaction history query | PASSED | 3ms |
| CASE-03 | Customer | Monthly spending summary | PASSED | 5ms |
| CASE-04 | Fraud | Suspicious activity analysis | PASSED | 113ms |
| CASE-05 | Fraud | Explain flagged transaction | PASSED | 19ms |
| CASE-06 | Credit | Loan eligibility evaluation | PASSED | 4ms |
| CASE-07 | Credit | Compare EMI scenarios | PASSED | 3ms |
| CASE-08 | Credit | Pending loan applications | PASSED | 5ms |
| CASE-09 | Compliance | KYC status verification | PASSED | 2ms |
| CASE-10 | Policy | Policy search RAG query | PASSED | 14ms |
| CASE-11 | Investigation | Cross-agent dossier build | PASSED | 116ms |

---

---

## 🐳 Containerized Deployment (Docker Compose)

Deploy the complete banking intelligence stack (FastAPI Backend + React Frontend + SQLite WAL + ML Model) with a single command:

```bash
docker compose up --build -d
```

- **Frontend Application**: `http://localhost`
- **Backend API Docs**: `http://localhost:8000/docs`

To shut down:
```bash
docker compose down
```

---

## ☁️ Cloud Deployment Guide

### Deploying to Render:
1. Connect this GitHub repository (`subikshan2006/ai-banking-intelligence`) to [Render](https://render.com).
2. Render will automatically detect [`render.yaml`](file:///C:/Users/admin/.gemini/antigravity/scratch/banking-ai-platform/render.yaml) (Blueprint specification) and provision both the Python web service and static frontend site.

### Deploying to Railway / Fly.io / AWS ECS:
1. Use the provided [`backend/Dockerfile`](file:///C:/Users/admin/.gemini/antigravity/scratch/banking-ai-platform/backend/Dockerfile) and [`frontend/Dockerfile`](file:///C:/Users/admin/.gemini/antigravity/scratch/banking-ai-platform/frontend/Dockerfile).
2. Configure `FRONTEND_ORIGIN` with your custom production domain in the backend environment variables.

---

## 📄 License & System Status

Operational enterprise banking intelligence system built with zero external API dependencies. All models, databases, and agents run 100% locally.
