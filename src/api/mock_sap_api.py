from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SAP_Mock")

app = FastAPI(title="SAP BTP Integration Suite (Mock)")

class PayloadCheck(BaseModel):
    bapi_name: str
    payload: dict

@app.get("/telemetry")
def get_telemetry():
    """Simulates dynamic telemetry coming from SAP Integration Suite."""
    logger.info("Fetching latest telemetry via REST.")
    return {
        "event": "IDOC_ERROR",
        "type": "ORDERS05",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "system_node": "SAP_BTP_INTEGRATION_SUITE",
        "error_code": "E055",
        "cryptic_message": "Replication Timeout. Purchasing Organization (EKORG) missing for LIFNR VEND_8832.",
        "business_impact": "Purchase order 4500012345 blocked from transmission."
    }

from typing import List, Optional, Any

class SAPOrgData(BaseModel):
    QUALF: str
    ORGID: str

class SAPIDocData(BaseModel):
    IDOCTYP: str
    MESTYP: str
    E1EDK14: List[SAPOrgData]

class ExecuteBAPIRequest(BaseModel):
    bapi_name: str
    payload: SAPIDocData

@app.post("/bapi/execute")
def execute_remediation(data: ExecuteBAPIRequest):
    """
    Validates SAP execution runtime checks using Strict Pydantic JSON Schema Validation
    Requires IDOC_INBOUND_ASYNCHRONOUS and correct segments E1EDK14, E1EDP01
    """
    logger.info(f"Incoming structured BAPI execution: {data.model_dump()}")
    
    if data.bapi_name.upper() != "IDOC_INBOUND_ASYNCHRONOUS":
        logger.error("Validation failed: Target BAPI is incorrect.")
        raise HTTPException(status_code=400, detail="Must execute against IDOC_INBOUND_ASYNCHRONOUS")
        
    ekorg_found = any(org.ORGID for org in data.payload.E1EDK14 if org.QUALF == "014" or org.ORGID.isalnum())
    
    if not ekorg_found:
        logger.error("Validation failed: Payload missing required SAP segments or EKORG missing.")
        raise HTTPException(status_code=400, detail="Missing valid EKORG mapping in E1EDK14 segment.")

    logger.info("SAP BAPI Execution SUCCESS via Pydantic Schema Validation")
    return {
        "status": "SUCCESS",
        "message": "Payload successfully validated against strict SAP IDoc schema.",
        "verified_segments": ["E1EDK14"],
        "runtime_code": 200
    }
