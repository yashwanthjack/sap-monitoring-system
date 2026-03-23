"""
Causal Planning Agent — Cognitive Engine.
Queries the Causal Knowledge Graph to verify downstream impact,
determine the correct fix, and generate the remediation plan payload.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.knowledge.graph import causal_kg
from src.ai.audit_logger import log_action


# ─── Fix payload templates (simulating BAPI call payloads) ─────────────
FIX_PAYLOADS = {
    "Create material in MDG": {
        "bapi": "BAPI_MATERIAL_SAVEDATA",
        "action": "create_material",
        "parameters": {
            "material_number": "100234",
            "description": "Auto-created Material (Self-Healing)",
            "material_group": "FERT",
            "unit_of_measure": "EA",
            "plant": "1000",
        },
    },
    "Create vendor in MDG": {
        "bapi": "BAPI_VENDOR_CREATE",
        "action": "create_vendor",
        "parameters": {
            "vendor_number": "1050",
            "name": "Auto-created Vendor (Self-Healing)",
            "country": "US",
            "purchasing_org": "0001",
        },
    },
    "Assign plant to purchasing org": {
        "bapi": "CONFIG_ASSIGNMENT",
        "action": "assign_config",
        "parameters": {
            "config_key": "PLANT_1000_PORG_0001",
            "config_value": "0001",
            "description": "Plant 1000 assigned to Purchasing Org 0001 (Auto-fix)",
        },
    },
    "Add unit of measure to T006": {
        "bapi": "BAPI_UOM_ADD",
        "action": "add_uom",
        "parameters": {
            "uom_code": "KG",
            "description": "Kilogram",
        },
    },
    "Delete duplicate PO entry in EKKO": {
        "bapi": "BAPI_PO_DELETE",
        "action": "delete_duplicate_po",
        "parameters": {
            "po_number": "4500001234",
        },
    },
    "Unblock GL account": {
        "bapi": "BAPI_GL_ACC_CHANGE",
        "action": "unblock_gl",
        "parameters": {
            "gl_account": "400000",
            "company_code": "1000",
        },
    },
    "Assign source of supply to material": {
        "bapi": "BAPI_SOURCEDETERMIN_GET",
        "action": "assign_source",
        "parameters": {
            "material_number": "100230",
            "plant": "1000",
            "vendor_number": "1040",
        },
    },
    "Configure tax code for country": {
        "bapi": "BAPI_TAX_CONFIG",
        "action": "config_tax",
        "parameters": {
            "tax_code": "V1",
            "country": "US",
        },
    },
    "Create customer in MDG": {
        "bapi": "BAPI_CUSTOMER_CREATE",
        "action": "create_customer",
        "parameters": {
            "customer_number": "500010",
            "name": "Auto-created Customer (Self-Healing)",
        },
    },
}


def plan_fix(diagnosis: dict) -> dict:
    """
    Use the Causal Knowledge Graph to:
    1. Verify downstream impact of the error
    2. Identify the fix from the graph
    3. Generate a BAPI execution payload

    Args:
        diagnosis: Output from the Diagnostic Agent.

    Returns:
        dict with the remediation plan.
    """
    kg_node = diagnosis.get("kg_node")
    root_causes = diagnosis.get("root_causes_list", [])
    log_id = diagnosis.get("log_id", "unknown")

    if not kg_node:
        result = {
            "status": "NO_PLAN",
            "message": "Cannot create remediation plan — no matching node in the Causal Knowledge Graph.",
            "fix": None,
            "payload": None,
            "downstream_impact": [],
            "causal_chain": [],
        }
        log_action(
            agent="Causal Planning Agent",
            action="PLAN_GENERATION",
            details="No plan generated — missing KG node mapping.",
            status="NO_ACTION",
            log_id=log_id,
        )
        return result

    # Step 1: Query downstream impact
    downstream_impact = causal_kg.get_downstream_impact(kg_node)

    # Step 2: Find the recommended fix for the root cause
    recommended_fix = None
    for rc in root_causes:
        fix = causal_kg.get_fix_for_cause(rc)
        if fix:
            recommended_fix = fix
            break

    # Step 3: Build the causal chain narrative
    causal_chain = []
    for rc in root_causes:
        impacts = causal_kg.get_downstream_impact(rc)
        chain = [rc] + [imp["affected"] for imp in impacts]
        causal_chain.append(" → ".join(chain))

    # Step 4: Generate the BAPI payload
    payload = None
    if recommended_fix and recommended_fix in FIX_PAYLOADS:
        payload = FIX_PAYLOADS[recommended_fix]

    result = {
        "status": "PLAN_READY",
        "message": f"Remediation plan generated. Fix: '{recommended_fix}'.",
        "fix_name": recommended_fix,
        "payload": payload,
        "downstream_impact": downstream_impact,
        "causal_chain": causal_chain,
        "root_causes": root_causes,
        "verified_by_kg": True,
    }

    # Step 5: Audit the planning action
    log_action(
        agent="Causal Planning Agent",
        action="PLAN_GENERATION",
        details=f"Fix: {recommended_fix} | Downstream impact: {len(downstream_impact)} entities | "
                f"Chain: {'; '.join(causal_chain)}",
        status="SUCCESS",
        log_id=log_id,
    )

    return result
