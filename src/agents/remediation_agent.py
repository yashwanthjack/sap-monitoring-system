"""
Remediation & Governance Agent — Execution & Governance Layer.
Applies the fix payload to the SAP simulator, enforces LeanIX/BRF+ policy checks,
and logs everything to the audit trail.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.execution import sap_simulator
from src.ai.audit_logger import log_action


# ─── Governance Policy Rules (simulating BRF+ / LeanIX) ───────────────
GOVERNANCE_POLICIES = {
    "create_material": {
        "allowed": True,
        "requires_approval": False,
        "max_auto_create_per_hour": 10,
        "description": "Auto-creation of materials is permitted for self-healing workflows.",
    },
    "create_vendor": {
        "allowed": True,
        "requires_approval": True,
        "max_auto_create_per_hour": 5,
        "description": "Vendor creation requires governance approval. Auto-approved in self-healing mode.",
    },
    "assign_config": {
        "allowed": True,
        "requires_approval": False,
        "max_auto_create_per_hour": 20,
        "description": "Configuration assignments are permitted.",
    },
    "add_uom": {
        "allowed": True,
        "requires_approval": False,
        "max_auto_create_per_hour": 50,
        "description": "Unit of measure additions are low-risk operations.",
    },
    "delete_duplicate_po": {
        "allowed": True,
        "requires_approval": True,
        "max_auto_create_per_hour": 3,
        "description": "PO deletion is a sensitive operation. Auto-approved with audit in self-healing mode.",
    },
}


def _check_governance(action: str) -> dict:
    """
    Simulate LeanIX / BRF+ governance policy check.
    Returns whether the action is authorized.
    """
    policy = GOVERNANCE_POLICIES.get(action)
    if not policy:
        return {
            "authorized": False,
            "reason": f"No governance policy defined for action '{action}'.",
            "policy": None,
        }

    if not policy["allowed"]:
        return {
            "authorized": False,
            "reason": f"Action '{action}' is blocked by governance policy.",
            "policy": policy,
        }

    approval_note = ""
    if policy["requires_approval"]:
        approval_note = " (Auto-approved in self-healing mode — governance override)"

    return {
        "authorized": True,
        "reason": f"Action '{action}' authorized.{approval_note}",
        "policy": policy,
    }


def execute_fix(plan: dict) -> dict:
    """
    Execute the remediation plan:
    1. Check governance policies (LeanIX/BRF+ simulation)
    2. Execute the BAPI payload on the SAP simulator
    3. Record everything to the audit trail

    Args:
        plan: Output from the Causal Planning Agent.

    Returns:
        dict with the execution result.
    """
    log_id = plan.get("log_id", "unknown")

    if plan.get("status") != "PLAN_READY" or not plan.get("payload"):
        result = {
            "status": "NO_EXECUTION",
            "message": "No executable plan available.",
            "governance_check": "N/A",
            "bapi_result": None,
        }
        log_action(
            agent="Remediation & Governance Agent",
            action="EXECUTION_SKIPPED",
            details="No executable plan was provided.",
            status="SKIPPED",
            governance_check="N/A",
            log_id=log_id,
        )
        return result

    payload = plan["payload"]
    action = payload["action"]
    params = payload["parameters"]
    bapi_name = payload["bapi"]

    # ── Step 1: Governance Check ──────────────────────────────────
    gov_check = _check_governance(action)

    log_action(
        agent="Remediation & Governance Agent",
        action="GOVERNANCE_CHECK",
        details=f"Action: {action} | Authorized: {gov_check['authorized']} | {gov_check['reason']}",
        status="PASSED" if gov_check["authorized"] else "BLOCKED",
        governance_check="PASSED" if gov_check["authorized"] else "FAILED",
        log_id=log_id,
    )

    if not gov_check["authorized"]:
        return {
            "status": "BLOCKED",
            "message": f"Governance policy blocked execution: {gov_check['reason']}",
            "governance_check": "FAILED",
            "bapi_result": None,
        }

    # ── Step 2: Execute BAPI on SAP Simulator ─────────────────────
    bapi_result = None
    try:
        if action == "create_material":
            bapi_result = sap_simulator.bapi_material_create(**params)
        elif action == "create_vendor":
            bapi_result = sap_simulator.bapi_vendor_create(**params)
        elif action == "assign_config":
            bapi_result = sap_simulator.bapi_config_assign(**params)
        elif action == "add_uom":
            bapi_result = sap_simulator.bapi_uom_add(**params)
        elif action == "delete_duplicate_po":
            bapi_result = sap_simulator.bapi_po_delete_duplicate(**params)
        else:
            bapi_result = {"status": "ERROR", "message": f"Unknown action: {action}"}
    except Exception as e:
        bapi_result = {"status": "ERROR", "message": str(e)}

    # ── Step 3: Audit the execution ───────────────────────────────
    exec_status = bapi_result.get("status", "UNKNOWN") if bapi_result else "ERROR"

    log_action(
        agent="Remediation & Governance Agent",
        action=f"BAPI_EXECUTION ({bapi_name})",
        details=f"Params: {params} | Result: {bapi_result.get('message', 'N/A') if bapi_result else 'N/A'}",
        status=exec_status,
        governance_check="PASSED",
        log_id=log_id,
    )

    resolved = exec_status == "SUCCESS"

    return {
        "status": "RESOLVED" if resolved else "EXECUTION_FAILED",
        "message": bapi_result.get("message", "") if bapi_result else "Execution failed.",
        "governance_check": "PASSED",
        "bapi_name": bapi_name,
        "bapi_result": bapi_result,
        "fix_applied": plan.get("fix_name", ""),
        "resolved": resolved,
    }
