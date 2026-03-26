"""
Diagnostic Agent — Intelligent Error Interception.
Reads SAP logs, translates cryptic error codes into human-readable business context,
and discovers the root cause.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.knowledge.graph import causal_kg
from src.ai.audit_logger import log_action


# ─── SAP Error Translation Knowledge Base ──────────────────────────────
ERROR_TRANSLATIONS = {
    "MATMAS": {
        "ED_51": "Material master IDoc failed — the material referenced does not exist in the MDG hub system. "
                 "Business Impact: Material cannot be replicated to connected ERP systems, blocking procurement and production.",
        "ED_56": "Material master IDoc processing incomplete — a required unit of measure is missing from the T006 table. "
                 "Business Impact: Material data is inconsistent across systems.",
    },
    "ORDERS05": {
        "ED_51": "Purchase Order IDoc failed — the vendor referenced does not exist in the MDG system. "
                 "Business Impact: Purchase orders cannot be created, blocking supply chain operations.",
    },
    "DBSQL_SQL_ERROR": {
        "DBSQL_SQL_ERROR": "ABAP short dump due to database SQL error — duplicate key violation in transaction table. "
                           "Business Impact: Critical transaction failure, potential data corruption.",
    },
    "REPLICATION_TIMEOUT": {
        "MDG_REPL_408": "MDG replication timeout — data governance change request failed after maximum retries. "
                        "Business Impact: Master data is out of sync between MDG hub and satellite systems.",
    },
    "BAPI_PO_CREATE1": {
        "06_311": "BAPI purchase order creation failed — organizational assignment missing (plant not assigned to purchasing org). "
                  "Business Impact: Procurement process blocked for the affected plant.",
    },
    "POSTING_ILLEGAL_STATEMENT": {
        "GL_BLOCK": "ABAP short dump: Posting blocked for General Ledger account. "
                    "Business Impact: Financial document posting failed, blocking month-end closing.",
    },
    "BAPI_PR_CREATE": {
        "06_050": "BAPI Purchase Requisition creation failed — No valid source of supply (vendor/contract) found for the material. "
                  "Business Impact: Automated procurement process broken.",
    },
    "BAPI_INCOMINGINVOICE_CREATE": {
        "M8_082": "BAPI Invoice posting failed — Tax code inconsistency or missing tax configuration for the country. "
                  "Business Impact: Accounts Payable process delayed, vendor payments blocked.",
    },
    "DEBMAS": {
        "ED_51": "Customer Master IDoc failed — The customer record does not exist in the MDG system. "
                 "Business Impact: Sales orders cannot be created for new customers.",
    },
}

# ─── Root cause mapping (error subtype → causal KG node name) ──────────
ERROR_TO_KG_NODE = {
    ("IDOC", "MATMAS", "ED_51"): "MATMAS IDoc failure",
    ("IDOC", "MATMAS", "ED_56"): "MATMAS IDoc incomplete",
    ("IDOC", "ORDERS05", "ED_51"): "ORDERS05 IDoc failure",
    ("ABAP_DUMP", "DBSQL_SQL_ERROR", "DBSQL_SQL_ERROR"): "ABAP DBSQL_SQL_ERROR dump",
    ("MDG_ERROR", "REPLICATION_TIMEOUT", "MDG_REPL_408"): "MDG replication timeout",
    ("BAPI_ERROR", "BAPI_PO_CREATE1", "06_311"): "BAPI_PO_CREATE1 error",
    ("ABAP_DUMP", "POSTING_ILLEGAL_STATEMENT", "GL_BLOCK"): "GL account blocked",
    ("BAPI_ERROR", "BAPI_PR_CREATE", "06_050"): "PR creation - no source",
    ("BAPI_ERROR", "BAPI_INCOMINGINVOICE_CREATE", "M8_082"): "Invoice tax mismatch",
    ("IDOC", "DEBMAS", "ED_51"): "DEBMAS IDoc failure",
}


def diagnose(log_entry: dict) -> dict:
    """
    Perform Intelligent Error Interception on an SAP log entry.

    Returns:
        dict with keys:
        - original_log: the raw SAP log
        - human_readable: translated business meaning
        - root_cause: the identified root cause
        - kg_node: the matching node in the Causal Knowledge Graph
        - severity: severity assessment
    """
    error_type = log_entry.get("type", "")
    subtype = log_entry.get("subtype", "")
    message_code = log_entry.get("message_code", "")
    raw_log = log_entry.get("raw_log", "")
    log_id = log_entry.get("id", "unknown")

    # Step 1: Translate the cryptic log into human-readable meaning
    translation = "Unknown SAP error — manual investigation required."
    if subtype in ERROR_TRANSLATIONS:
        translation = ERROR_TRANSLATIONS[subtype].get(message_code, translation)

    # Step 2: Map to the Causal Knowledge Graph node
    kg_key = (error_type, subtype, message_code)
    kg_node = ERROR_TO_KG_NODE.get(kg_key, None)

    # Step 3: Use the CausalKG to trace the root cause
    root_causes = []
    if kg_node:
        root_causes = causal_kg.get_root_cause(kg_node)

    root_cause_str = ", ".join(root_causes) if root_causes else "Root cause could not be determined automatically."

    result = {
        "original_log": raw_log,
        "human_readable": translation,
        "root_cause": root_cause_str,
        "root_causes_list": root_causes,
        "kg_node": kg_node,
        "severity": log_entry.get("severity", "UNKNOWN"),
        "business_object": log_entry.get("business_object", "Unknown"),
        "log_id": log_id,
    }

    # Step 4: Audit the diagnostic action
    log_action(
        agent="Diagnostic Agent",
        action="ERROR_DIAGNOSIS",
        details=f"Diagnosed: {subtype} ({message_code}) → Root cause: {root_cause_str}",
        status="SUCCESS",
        log_id=log_id,
    )

    return result
