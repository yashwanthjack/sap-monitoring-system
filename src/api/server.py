"""
FastAPI Server — SAP Self-Healing MVP API.
Provides REST endpoints to trigger the self-healing pipeline,
fetch audit logs, SAP DB state, knowledge graph data, and error scenarios.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from src.ai.crew_orchestrator import run_self_healing_pipeline
from src.monitor.log_reader import get_all_scenarios, generate_log_entry
from src.knowledge.graph import causal_kg
from src.execution.sap_simulator import get_db_state, reset_db
from src.ai.audit_logger import get_audit_log, clear_audit_log

app = FastAPI(
    title="SAP Self-Healing MVP",
    description="Causal-Agentic Self-Healing SAP Ecosystem — Atos Srijan",
    version="1.0.0",
)

# Allow Streamlit / React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Models ────────────────────────────────────────────────────

class HealRequest(BaseModel):
    scenario_index: Optional[int] = None


# ─── Endpoints ─────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "SAP Self-Healing MVP",
        "status": "running",
        "description": "Causal-Agentic Self-Healing SAP Ecosystem",
    }


@app.get("/api/scenarios")
def list_scenarios():
    """List all available SAP error scenarios."""
    return {"scenarios": get_all_scenarios()}


@app.post("/api/heal")
def trigger_healing(request: HealRequest):
    """
    Trigger the full self-healing pipeline.
    Optionally specify a scenario_index to select a specific error scenario.
    """
    result = run_self_healing_pipeline(scenario_index=request.scenario_index)
    return result


@app.get("/api/heal/random")
def trigger_random_healing():
    """Trigger the pipeline with a random error scenario."""
    result = run_self_healing_pipeline()
    return result


@app.get("/api/audit")
def fetch_audit_log(limit: int = 50):
    """Retrieve the audit trail."""
    return {"audit_log": get_audit_log(limit)}


@app.get("/api/db-state")
def fetch_db_state():
    """Get the current state of the simulated SAP database."""
    return {"db_state": get_db_state()}


@app.get("/api/knowledge-graph")
def fetch_knowledge_graph():
    """Get the full causal knowledge graph data for visualization."""
    return {"graph": causal_kg.get_graph_data()}


@app.post("/api/reset")
def reset_system():
    """Reset the SAP simulator database and clear audit logs."""
    reset_db()
    clear_audit_log()
    return {"status": "reset", "message": "SAP simulator and audit log have been reset."}
