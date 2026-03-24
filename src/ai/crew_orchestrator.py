"""
Crew Orchestrator — Multi-Agent Pipeline.
Assembles the 3-agent self-healing pipeline:
  Diagnostic Agent → Causal Planning Agent → Remediation & Governance Agent

This orchestrator runs the agents sequentially, passing context between them,
simulating the CrewAI multi-agent orchestration pattern.
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
import json
from crewai.tools import tool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.monitor.log_reader import generate_log_entry
from src.agents.diagnostic_agent import diagnose
from src.agents.planner_agent import plan_fix
from src.agents.remediation_agent import execute_fix
from src.ai.audit_logger import log_action

load_dotenv()

# --- THE HACKATHON CHEAT CODE ---
# Tricking CrewAI into thinking Groq is OpenAI
os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY")
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
os.environ["OPENAI_MODEL_NAME"] = "llama-3.1-8b-instant"

# --- THE EYES (The Tool) ---

@tool("Intercept SAP Telemetry")
def intercept_sap_telemetry(dummy: str = "") -> str:
    """Always use this tool to read the latest intercepted SAP error logs, IDocs, or ABAP dumps."""
    
    # This is the exact fake error your AI will fix during the live demo
    mock_idoc_failure = {
        "event": "IDOC_ERROR",
        "type": "ORDERS05",
        "timestamp": "2026-03-24T09:50:00Z",
        "system_node": "SAP_PRD_HANA",
        "error_code": "E055",
        "cryptic_message": "Replication Timeout. VKORG missing for LIFNR VEND_8832.",
        "business_impact": "Purchase order 4500012345 blocked from transmission."
    }
    return json.dumps(mock_idoc_failure)

# ── Step 3: Define CrewAI Agents with the LLM brain ──────────────────
diagnostic_agent = Agent(
    role='SAP Diagnostic Specialist',
    goal='Analyze system logs and identify root causes of failures',
    backstory=(
        'You are an expert SAP system administrator with 15+ years of experience '
        'in SAP Basis, ABAP, and middleware (PI/PO). You specialize in reading '
        'cryptic SAP error logs and translating them into clear root-cause analyses.'
    ),
    tools=[intercept_sap_telemetry],
    allow_delegation=False
)

governance_agent = Agent(
    role='SAP Causal Planning Specialist',
    goal='Create remediation plans based on causal analysis of SAP system failures',
    backstory=(
        'You are a senior SAP solution architect who designs fix strategies by '
        'tracing causal chains through the Knowledge Graph. You determine downstream '
        'impact and select the optimal BAPI-level remediation for each failure.'
    ),
    allow_delegation=False
)

remediation_agent = Agent(
    role='SAP Remediation & Governance Specialist',
    goal='Execute remediation plans while enforcing governance policies',
    backstory=(
        'You are a governance-aware SAP operations engineer responsible for executing '
        'fixes via BAPI calls. You enforce LeanIX and BRF+ policies before any change '
        'is applied and maintain a complete audit trail of every action.'
    ),
    allow_delegation=False
)


def run_self_healing_pipeline(log_entry: dict | None = None, scenario_index: int | None = None) -> dict:
    """
    Execute the full self-healing pipeline:
      1. Generate/receive SAP error log
      2. Diagnostic Agent → root cause analysis
      3. Causal Planning Agent → fix planning with KG verification
      4. Remediation & Governance Agent → execute fix with policy checks

    Args:
        log_entry: An SAP log entry dict. If None, one will be generated.
        scenario_index: Index of the error scenario to simulate (if log_entry is None).

    Returns:
        dict with the full pipeline execution result.
    """
    pipeline_start = datetime.now().isoformat()

    # ── Step 0: Generate or use provided log ──────────────────────
    if log_entry is None:
        log_entry = generate_log_entry(scenario_index)

    log_id = log_entry.get("id", "unknown")

    log_action(
        agent="Pipeline Orchestrator",
        action="PIPELINE_START",
        details=f"Processing {log_entry.get('type', 'UNKNOWN')} error: {log_entry.get('subtype', 'N/A')}",
        status="IN_PROGRESS",
        log_id=log_id,
    )

    steps = []

    # ── Step 1: Diagnostic Agent ──────────────────────────────────
    step1_start = datetime.now().isoformat()
    diagnosis = diagnose(log_entry)
    steps.append({
        "step": 1,
        "agent": "Diagnostic Agent",
        "action": "Error Interception & Root Cause Analysis",
        "started_at": step1_start,
        "completed_at": datetime.now().isoformat(),
        "input": {
            "type": log_entry.get("type"),
            "subtype": log_entry.get("subtype"),
            "raw_log": log_entry.get("raw_log"),
        },
        "output": {
            "human_readable": diagnosis.get("human_readable"),
            "root_cause": diagnosis.get("root_cause"),
            "severity": diagnosis.get("severity"),
        },
        "status": "✅ Complete",
    })

    # ── Step 2: Causal Planning Agent ─────────────────────────────
    step2_start = datetime.now().isoformat()
    plan = plan_fix(diagnosis)
    plan["log_id"] = log_id  # carry forward for audit
    steps.append({
        "step": 2,
        "agent": "Causal Planning Agent",
        "action": "Causal Reasoning & Fix Planning",
        "started_at": step2_start,
        "completed_at": datetime.now().isoformat(),
        "input": {
            "root_cause": diagnosis.get("root_cause"),
            "kg_node": diagnosis.get("kg_node"),
        },
        "output": {
            "fix": plan.get("fix_name"),
            "causal_chain": plan.get("causal_chain"),
            "downstream_impact_count": len(plan.get("downstream_impact", [])),
            "verified_by_kg": plan.get("verified_by_kg", False),
        },
        "status": "✅ Complete" if plan.get("status") == "PLAN_READY" else "⚠️ No Plan",
    })

    # ── Step 3: Remediation & Governance Agent ────────────────────
    step3_start = datetime.now().isoformat()
    execution = execute_fix(plan)
    steps.append({
        "step": 3,
        "agent": "Remediation & Governance Agent",
        "action": "Governance Check & BAPI Execution",
        "started_at": step3_start,
        "completed_at": datetime.now().isoformat(),
        "input": {
            "fix": plan.get("fix_name"),
            "bapi": plan.get("payload", {}).get("bapi") if plan.get("payload") else None,
        },
        "output": {
            "governance_check": execution.get("governance_check"),
            "bapi_result": execution.get("bapi_result", {}).get("message") if execution.get("bapi_result") else None,
            "resolved": execution.get("resolved", False),
        },
        "status": "✅ Resolved" if execution.get("resolved") else "❌ Failed",
    })

    pipeline_end = datetime.now().isoformat()
    resolved = execution.get("resolved", False)

    # Final audit entry
    log_action(
        agent="Pipeline Orchestrator",
        action="PIPELINE_COMPLETE",
        details=f"Resolved: {resolved} | Fix: {plan.get('fix_name', 'None')}",
        status="RESOLVED" if resolved else "UNRESOLVED",
        log_id=log_id,
    )

    return {
        "pipeline_id": log_id,
        "started_at": pipeline_start,
        "completed_at": pipeline_end,
        "log_entry": log_entry,
        "diagnosis": diagnosis,
        "plan": {
            "fix_name": plan.get("fix_name"),
            "causal_chain": plan.get("causal_chain"),
            "downstream_impact": plan.get("downstream_impact"),
            "verified_by_kg": plan.get("verified_by_kg", False),
        },
        "execution": execution,
        "steps": steps,
        "resolved": resolved,
        "summary": (
            f"{'✅ RESOLVED' if resolved else '❌ UNRESOLVED'}: "
            f"{log_entry.get('subtype', 'Unknown')} error → "
            f"Root cause: {diagnosis.get('root_cause', 'Unknown')} → "
            f"Fix: {plan.get('fix_name', 'None')} → "
            f"{'Applied successfully' if resolved else 'Execution failed'}"
        ),
    }


from crewai import Task, Crew, Process

# --- THE SELF-HEALING JOBS ---

diagnose_task = Task(
    description="Intercept the latest SAP telemetry stream. Identify any cryptic ABAP short dumps or IDoc failures (e.g., ORDERS05, MATMAS) and determine the exact root cause.",
    expected_output="A precise root-cause analysis translating the cryptic SAP error into actionable context.",
    agent=diagnostic_agent 
)

remediate_task = Task(
    description="Based on the root cause, automatically generate the exact BAPI payload or data correction required to self-heal the system. Do not ask for IT intervention.",
    expected_output="The exact JSON payload or technical command required to fix the error.",
    agent=remediation_agent
)

audit_task = Task(
    description="Review the generated remediation payload against zero-trust security policies. Verify the downstream impact and ensure segregation of duties before autonomous execution.",
    expected_output="A final 'APPROVED' execution payload and a LeanIX-compliant audit log entry.",
    agent=governance_agent # Remember to rename your planner_agent to this!
)

# --- THE AUTONOMOUS PIPELINE ---

sap_self_healing_crew = Crew(
    agents=[diagnostic_agent, remediation_agent, governance_agent],
    tasks=[diagnose_task, remediate_task, audit_task],
    process=Process.sequential, 
    verbose=True 
)

if __name__ == '__main__':
    print('🚀 Intercepting SAP Telemetry Stream...')
    print('--------------------------------------------------')
    
    # This fires the first agent
    final_result = sap_self_healing_crew.kickoff()
    
    print('\n==================================================')
    print('✅ FINAL GOVERNANCE APPROVED EXECUTION:')
    print('==================================================')
    print(final_result)
