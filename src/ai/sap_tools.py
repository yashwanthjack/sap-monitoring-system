import os
import requests
import json
import logging
from crewai.tools import tool

# Configure structured logging
logger = logging.getLogger("SAP_Tools")

SAP_BASE_URL = os.environ.get("SAP_BTP_URL", "http://localhost:8000")

def get_sap_oauth_token():
    """Retrieve an OAuth token using SAP Destination or Client Credentials."""
    token_url = os.environ.get("SAP_OAUTH_URL")
    client_id = os.environ.get("SAP_CLIENT_ID")
    client_secret = os.environ.get("SAP_CLIENT_SECRET")
    
    if not (token_url and client_id and client_secret):
        logger.warning("Missing SAP credentials in .env. Falling back to local/mock context.")
        return "MOCK_TOKEN"
        
    try:
        response = requests.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        logger.error(f"Failed to get OAuth token: {str(e)}")
        return "MOCK_TOKEN"

@tool("Fetch Live Telemetry")
def fetch_telemetry(dummy: str = "") -> str:
    """Always use this tool to fetch actual live telemetry via REST API from SAP Integration Suite."""
    from src.api.ws_manager import trigger_dashboard_event
    logger.info("📡 Tool invoked: Fetching live telemetry...")
    token = get_sap_oauth_token()
    headers = {"Authorization": f"Bearer {token}"} if token != "MOCK_TOKEN" else {}
    try:
        url = f"{SAP_BASE_URL}/telemetry" if "localhost" in SAP_BASE_URL else f"{SAP_BASE_URL}/api/v1/telemetry"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        trigger_dashboard_event("INCOMING_ERROR", data={"message": "Fetched live telemetry via API", "payload": data})
        return json.dumps(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching telemetry: {str(e)}")
        return json.dumps({"error": f"Failed to fetch telemetry: {str(e)}"})

@tool("Execute Remediation Payload")
def execute_remediation(payload_string: str) -> str:
    """
    Executes an action layer API call using an IDoc or BAPI payload on SAP BTP.
    """
    from src.api.ws_manager import trigger_dashboard_event
    logger.info("⚙️ Tool invoked: Executing remediation payload...")
    token = get_sap_oauth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token != "MOCK_TOKEN" else {"Content-Type": "application/json"}
    
    try:
        try:
            cleaned = payload_string.replace('```json', '').replace('```', '').strip()
            payload = json.loads(cleaned)
        except Exception as e:
            trigger_dashboard_event("ERROR", data={"message": "Failed to parse payload JSON from agent."})
            return json.dumps({"execute_status": "FAILED", "reason": "Invalid JSON format. You MUST regenerate successfully parseable JSON."})

        inner_payload = payload.get("payload", payload)
        
        trigger_dashboard_event("WARNING", data={"message": "Executing payload (Sending to SAP Action Layer)...", "payload": inner_payload})
        
        url = f"{SAP_BASE_URL}/bapi/execute" if "localhost" in SAP_BASE_URL else f"{SAP_BASE_URL}/api/v1/bapi/execute"
        
        response = requests.post(
            url, 
            json={"bapi_name": "IDOC_INBOUND_ASYNCHRONOUS", "payload": inner_payload}, 
            headers=headers,
            timeout=10
        )
        
        if response.status_code in (200, 201, 202):
            trigger_dashboard_event("SUCCESS", data={"message": "Execution SUCCESS (200)", "response": response.json()})
            return json.dumps({"execute_status": "SUCCESS", "response": response.json(), "api_code": response.status_code})
            
        elif response.status_code == 422:
            trigger_dashboard_event("ERROR", data={"message": "Execution FAILED - Invalid Schema."})
            return json.dumps({
                "execute_status": "RETRY_REQUIRED", 
                "reason": "422 Unprocessable Entity - Invalid SAP Schema. You MUST strictly regenerate the payload using the exact schema example provided in your prompt, including 'IDOCTYP', 'MESTYP', and 'E1EDK14' array."
            })
        elif response.status_code == 400:
            trigger_dashboard_event("ERROR", data={"message": "Execution FAILED - HTTP 400 Bad Request."})
            return json.dumps({
                "execute_status": "RETRY_REQUIRED", 
                "reason": f"API Validation Failed (HTTP 400): {response.text}. Correct your JSON string and retry."
            })
        else:
            trigger_dashboard_event("ERROR", data={"message": f"Execution FAILED - HTTP {response.status_code}"})
            return json.dumps({"execute_status": "FAILED", "reason": response.text, "api_code": response.status_code})

    except Exception as e:
        trigger_dashboard_event("ERROR", data={"message": f"Execution FAILED - Exception: {str(e)}"})
        logger.error(f"Execution Error: {str(e)}")
        return json.dumps({"execute_status": "ERROR", "reason": str(e)})
