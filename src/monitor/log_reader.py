"""
SAP Log Simulator — Simulates the SAP Integration Suite Telemetry Layer.
Generates realistic SAP error payloads: ABAP dumps, IDoc failures, MDG errors, BAPI errors.
"""

import random
import uuid
from datetime import datetime


# ─── Pre-defined SAP Error Scenarios ────────────────────────────────────────

SAP_ERROR_SCENARIOS = [
    {
        "id": None,
        "timestamp": None,
        "type": "IDOC",
        "subtype": "MATMAS",
        "system": "ERP_PRD_100",
        "message_code": "ED_51",
        "raw_log": "IDoc MATMAS05 0000000012345678 status 51: Application document not posted. "
                   "Segment E1MARAM: Material number 000000000000100234 does not exist in MDG hub.",
        "severity": "HIGH",
        "business_object": "Material",
        "transaction": "BD10",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "IDOC",
        "subtype": "ORDERS05",
        "system": "ERP_PRD_100",
        "message_code": "ED_51",
        "raw_log": "IDoc ORDERS05 0000000098765432 status 51: Application document not posted. "
                   "Segment E1EDK01: Vendor 0000001050 not found in MDG system.",
        "severity": "HIGH",
        "business_object": "PurchaseOrder",
        "transaction": "ME21N",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "ABAP_DUMP",
        "subtype": "DBSQL_SQL_ERROR",
        "system": "ERP_PRD_100",
        "message_code": "DBSQL_SQL_ERROR",
        "raw_log": "Short dump DBSQL_SQL_ERROR in program SAPMM06E at event START-OF-SELECTION. "
                   "Database error: SQL code -803. Duplicate key in table EKKO for PO 4500001234.",
        "severity": "CRITICAL",
        "business_object": "PurchaseOrder",
        "transaction": "ME21N",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "MDG_ERROR",
        "subtype": "REPLICATION_TIMEOUT",
        "system": "MDG_HUB_200",
        "message_code": "MDG_REPL_408",
        "raw_log": "MDG Replication timeout for Change Request CR-00789. "
                   "Material 000000000000100234 replication to ERP_PRD_100 failed after 3 retries. "
                   "Data model MM: Field MATKL (Material Group) is missing mandatory value.",
        "severity": "HIGH",
        "business_object": "Material",
        "transaction": "MDGIMG",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "BAPI_ERROR",
        "subtype": "BAPI_PO_CREATE1",
        "system": "ERP_PRD_100",
        "message_code": "06_311",
        "raw_log": "BAPI_PO_CREATE1 returned error: Message 06 311 — "
                   "Plant 1000 is not assigned to purchasing organization 0001. "
                   "Purchase order creation failed for vendor 0000001050.",
        "severity": "MEDIUM",
        "business_object": "PurchaseOrder",
        "transaction": "ME21N",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "IDOC",
        "subtype": "MATMAS",
        "system": "ERP_PRD_100",
        "message_code": "ED_56",
        "raw_log": "IDoc MATMAS05 0000000012349999 status 56: IDoc processing incomplete. "
                   "Segment E1MARAM: Unit of measure KG not found in table T006 for material 100235.",
        "severity": "MEDIUM",
        "business_object": "Material",
        "transaction": "BD10",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "ABAP_DUMP",
        "subtype": "POSTING_ILLEGAL_STATEMENT",
        "system": "ERP_PRD_100",
        "message_code": "GL_BLOCK",
        "raw_log": "Short dump POSTING_ILLEGAL_STATEMENT in program SAPLFACG. "
                   "GL Account 400000 is blocked for direct postings in company code 1000.",
        "severity": "HIGH",
        "business_object": "GLAccount",
        "transaction": "FB01",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "BAPI_ERROR",
        "subtype": "BAPI_PR_CREATE",
        "system": "ERP_PRD_100",
        "message_code": "06_050",
        "raw_log": "BAPI_PR_CREATE failed: No source of supply found for material 100230, plant 1000. "
                   "Purchase requisition 10000567 could not be created.",
        "severity": "MEDIUM",
        "business_object": "PurchaseRequisition",
        "transaction": "ME51N",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "BAPI_ERROR",
        "subtype": "BAPI_INCOMINGINVOICE_CREATE",
        "system": "ERP_PRD_100",
        "message_code": "M8_082",
        "raw_log": "BAPI_INCOMINGINVOICE_CREATE failed: Tax code V1 not defined for country US. "
                   "Invoice verification stopped for PO 4500001234.",
        "severity": "HIGH",
        "business_object": "Invoice",
        "transaction": "MIRO",
    },
    {
        "id": None,
        "timestamp": None,
        "type": "IDOC",
        "subtype": "DEBMAS",
        "system": "ERP_PRD_100",
        "message_code": "ED_51",
        "raw_log": "IDoc DEBMAS06 0000000055556666 status 51: Application document not posted. "
                   "Segment E1KNA1M: Customer 500010 does not exist in MDG system.",
        "severity": "HIGH",
        "business_object": "Customer",
        "transaction": "BD12",
    },
]


def generate_log_entry(scenario_index: int | None = None) -> dict:
    """
    Generate a single SAP error log entry.
    If scenario_index is provided, use that specific scenario.
    Otherwise, pick a random one.
    """
    if scenario_index is not None:
        scenario = SAP_ERROR_SCENARIOS[scenario_index % len(SAP_ERROR_SCENARIOS)]
    else:
        scenario = random.choice(SAP_ERROR_SCENARIOS)

    entry = dict(scenario)
    entry["id"] = str(uuid.uuid4())
    entry["timestamp"] = datetime.now().isoformat()
    return entry


def get_all_scenarios() -> list[dict]:
    """Return metadata about all available error scenarios."""
    return [
        {
            "index": i,
            "type": s["type"],
            "subtype": s["subtype"],
            "severity": s["severity"],
            "business_object": s["business_object"],
            "summary": s["raw_log"][:80] + "...",
        }
        for i, s in enumerate(SAP_ERROR_SCENARIOS)
    ]
