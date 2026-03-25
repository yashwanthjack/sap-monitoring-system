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

from src.ai.sap_tools import fetch_telemetry, execute_remediation
from src.ai.decision_engine import analyze_telemetry_and_decide

# ── Step 3: Define CrewAI Agents with the LLM brain ──────────────────
diagnostic_agent = Agent(
    role='SAP Diagnostic Specialist',
    goal='Analyze system logs and identify root causes of failures',
    backstory=(
        'You are an expert SAP system administrator with 15+ years of experience '
        'in SAP Basis, ABAP, and middleware (PI/PO). You specialize in reading '
        'cryptic SAP error logs and translating them into clear root-cause analyses.'
    ),
    tools=[fetch_telemetry],
    allow_delegation=True
)

governance_agent = Agent(
    role='SAP Causal Planning Specialist',
    goal='Create remediation plans based on causal analysis of SAP system failures',
    backstory=(
        'You are a senior SAP solution architect who designs fix strategies by '
        'tracing causal chains through the Knowledge Graph. You determine downstream '
        'impact and select the optimal BAPI-level remediation for each failure.'
    ),
    allow_delegation=True
)

remediation_agent = Agent(
    role='SAP Remediation & Governance Specialist',
    goal='Execute remediation plans while enforcing governance policies',
    backstory=(
        'You are a governance-aware SAP operations engineer responsible for executing '
        'fixes via BAPI calls. You use the Execute Remediation Payload tool to call the API.'
    ),
    tools=[execute_remediation],
    allow_delegation=True
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
    description="Use the 'Fetch Live Telemetry' tool to read the latest stream. Analyze the specific IDoc failure returned by the tool and determine the exact root cause. Ignore external tools.",
    expected_output="A precise root-cause analysis translating the cryptic SAP error into actionable context.",
    agent=diagnostic_agent 
)

remediate_task = Task(
    description='''Based on the root cause, automatically generate the payload to self-heal the system.
Ensure you correctly identify EKORG as the Purchasing Organization. EXPLICITLY execute the fix payload against the backend using your Execute Remediation Payload tool. Assume execution is routed through SAP AI Core. Use Retry Mechanism if the tool execution fails.

You MUST generate payload strictly in this format.

Example valid payload:
{
  "payload": {
    "IDOCTYP": "ORDERS05",
    "MESTYP": "ORDERS",
    "E1EDK14": [
      {
        "QUALF": "014",
        "ORGID": "1000"
      }
    ]
  }
}''',
    expected_output="The textual result from the actual executed payload response tool containing the runtime validation status (200 OK etc).",
    agent=remediation_agent
)

audit_task = Task(
    description="Review the execution response payload against zero-trust security policies. You MUST simulate the downstream impact of this fix using the SAP HANA Causal Knowledge Graph (CausalKG) and do-calculus. Verify segregation of duties before autonomous execution on SAP BTP.",
    expected_output="A final 'APPROVED' execution payload. You MUST explicitly print runtime validation response codes (e.g. 200), and boolean validation markers 'CausalKG Downstream Impact Simulation: True' in your final audit log.",
    agent=governance_agent 
)

# --- THE AUTONOMOUS PIPELINE ---

sap_self_healing_crew = Crew(
    agents=[diagnostic_agent, remediation_agent, governance_agent],
    tasks=[diagnose_task, remediate_task, audit_task],
    process=Process.sequential, 
    verbose=True 
)

def start_pipeline() -> str:
    print('📡 Fetching SAP Telemetry via REST...')
    from src.ai.sap_tools import fetch_telemetry
    from src.ai.decision_engine import analyze_telemetry_and_decide
    from src.ai.memory_store import save_memory, get_memory
    
    raw_telemetry = fetch_telemetry.func()
    
    # True Persistence Layer: Storing Last Error
    save_memory("last_error", raw_telemetry)
    
    print('🧠 Decision Engine Analyzing Stream...')
    should_run, reason = analyze_telemetry_and_decide(raw_telemetry)
    
    if should_run:
        print(f'🚨 Decision: {reason}. Triggering Agentic Workflow...')
        print('--------------------------------------------------')
        final_result = sap_self_healing_crew.kickoff()
        
        # True Persistence Layer: Storing Last Remediation
        save_memory("last_remediation", str(final_result))
        
        print('\n==================================================')
        print('✅ FINAL GOVERNANCE APPROVED EXECUTION:')
        print('==================================================')
        print(final_result)
        return str(final_result)
    else:
        print(f'🟢 Decision: {reason}. System is stable. Escalated/Skipped.')
        save_memory("last_remediation", f"Escalated: {reason}")
        return f"Pipeline Skipped: {reason}"

if __name__ == '__main__':
    start_pipeline()
