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

from src.ai.crew_orchestrator import start_pipeline
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


@app.get("/status")
def root():
    return {
        "name": "SAP Self-Healing Enterprise API",
        "status": "RUNNING",
        "orchestrator_node": "SAP AI Core Simulation",
        "description": "Causal-Agentic Self-Healing Engine"
    }

@app.post("/trigger")
def trigger_healing():
    """
    Triggers the new full autonomous decision engine and self-healing pipeline.
    """
    result = start_pipeline()
    return {"status": "SUCCESS", "message": "Pipeline completed", "pipeline_output": result}

@app.get("/logs")
def fetch_audit_log(limit: int = 50):
    """Retrieve the audit trail."""
    return {"audit_log": get_audit_log(limit)}
