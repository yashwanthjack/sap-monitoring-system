# 🛡️ Causal-Agentic Self-Healing SAP Ecosystem

**Atos Srijan Hackathon MVP**

A 3-agent self-healing system that automatically detects, diagnoses, and resolves SAP ERP/MDG errors using Causal AI and Multi-Agent Orchestration.

## Architecture

```
SAP Logs (Simulated)
     ↓
Agent 1: Diagnostic Agent       — Error interception & root cause analysis
     ↓
Agent 2: Causal Planning Agent  — Knowledge Graph reasoning & fix planning
     ↓
Agent 3: Remediation Agent      — Governance check & BAPI execution
     ↓
Audit Log + SAP DB Update
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agents | CrewAI |
| Knowledge Graph | NetworkX |
| Database | SQLite |
| API | FastAPI |
| Frontend | Streamlit |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the demo dashboard
streamlit run demo/run_demo.py

# Or run the FastAPI server
uvicorn src.api.server:app --reload --port 8000

# Or run the CLI test
python -m src.ai.crew_orchestrator
```

## Project Structure

```
SAP/
├── src/
│   ├── monitor/
│   │   └── log_reader.py          # SAP log simulator
│   ├── agents/
│   │   ├── diagnostic_agent.py    # Agent 1: Error diagnosis
│   │   ├── planner_agent.py       # Agent 2: Causal planning
│   │   └── remediation_agent.py   # Agent 3: Fix execution
│   ├── knowledge/
│   │   └── graph.py               # Causal Knowledge Graph
│   ├── execution/
│   │   └── sap_simulator.py       # Mock SAP BAPI layer
│   ├── ai/
│   │   ├── crew_orchestrator.py   # Pipeline orchestrator
│   │   └── audit_logger.py        # Governance audit trail
│   └── api/
│       └── server.py              # FastAPI endpoints
├── demo/
│   └── run_demo.py                # Streamlit dashboard
├── logs/                          # SQLite databases
├── requirements.txt
└── README.md
```
