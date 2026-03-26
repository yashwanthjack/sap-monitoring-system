# 🛡️ Causal-Agentic Self-Healing SAP Ecosystem (v1)

**Atos Srijan Hackathon MVP — Enterprise Edition**

An autonomous, AI-driven self-healing pipeline for SAP BTP. It intercept events from SAP Event Mesh, analyzes them using a Causal Reasoning Decision Engine, and deploys CrewAI agents to perform autonomous BAPI remediation via SAP AI Core.

## 🚀 Key Features (v1)

- **Autonomous Decision Engine**: Intelligent triage using `llama-3.3-70b-versatile` with confidence scoring.
- **CrewAI Orchestration**: 3-agent pipeline (Diagnostic, Planner, Remediation) with shared context and tool-use.
- **Real-Time WebSocket Dashboard**: A premium, minimal dark-mode UI for live monitoring of agent execution logs.
- **Persistence Layer**: Robust state tracking with SQLAlchemy (PostgreSQL-ready).
- **SAP BTP Integration**: Real OAuth2/OData API integration endpoints for telemetry and action layers.
- **Observability**: OpenTelemetry tracing for pipeline analysis.

## 🏗️ Architecture

```text
SAP BTP / Event Mesh
      ↓ (Webhook / RabbitMQ)
FastAPI Gateway
      ↓
Decision Engine (Triage & Confidence < 0.7 Escalate)
      ↓
CrewAI Pipeline:
  1. Diagnostic Agent  → Error interception & root cause
  2. Planner Agent     → Causal Reasoning & Fix Strategy
  3. Remediation Agent → Execution & Governance Audit
      ↓
SAP Action Layer (BAPI/IDoc Execute)
      ↓
WebSocket Dashboard (Live Streaming)
```

## 🛠️ Tech Stack

- **Agents**: CrewAI + Groq (Llama 3.3 70B)
- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLAlchemy + SQLite (Dev) / PostgreSQL (Prod)
- **UI**: Vanilla JS + HTML5 + WebSockets (Minimal Dark Theme)
- **Messaging**: RabbitMQ (Optional Event Mesh interface)

## 🏃 Quick Start

1. **Environment Setup**:
   ```bash
   pip install -r requirements.txt
   # Ensure GROQ_API_KEY is in your .env
   ```

2. **Launch Server**:
   ```bash
   uvicorn src.api.server:app --reload
   ```

3. **Access Dashboard**:
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

4. **Trigger Test**:
   Click "Simulate BAPI Error" on the dashboard to see the full autonomous flow in real-time.

## 📂 Project Structure

- `src/ai/crew_orchestrator.py`: The heart of the multi-agent pipeline.
- `src/ai/decision_engine.py`: LLM-based triage and strategy selector.
- `src/ai/sap_tools.py`: Real SAP API integration tools.
- `src/api/server.py`: FastAPI routes & WebSocket broadcasting.
- `src/api/index.html`: The real-time dashboard UI.
- `src/api/ws_manager.py`: Decoupled WebSocket message broker.

## 📜 Branching
- `v1-dashboard-update`: Current stable release with the minimal dark dashboard.

