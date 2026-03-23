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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.monitor.log_reader import generate_log_entry
from src.agents.diagnostic_agent import diagnose
from src.agents.planner_agent import plan_fix
from src.agents.remediation_agent import execute_fix
from src.ai.audit_logger import log_action


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


if __name__ == "__main__":
    # Quick test — run all scenarios
    import json
    from src.monitor.log_reader import SAP_ERROR_SCENARIOS

    print("=" * 80)
    print("  SAP Self-Healing Pipeline — Test Run")
    print("=" * 80)

    for i in range(len(SAP_ERROR_SCENARIOS)):
        print(f"\n{'─' * 60}")
        print(f"  Scenario {i + 1}")
        print(f"{'─' * 60}")
        result = run_self_healing_pipeline(scenario_index=i)
        print(f"  {result['summary']}")
        for step in result["steps"]:
            print(f"    Step {step['step']}: {step['agent']} — {step['status']}")

    print(f"\n{'=' * 80}")
    print("  All scenarios complete!")
    print(f"{'=' * 80}")
