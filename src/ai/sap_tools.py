import requests
import json
import logging
from crewai.tools import tool

# Configure structured logging
logger = logging.getLogger("SAP_Tools")

SAP_MOCK_BASE_URL = "http://localhost:8000"

@tool("Fetch Live Telemetry")
def fetch_telemetry(dummy: str = "") -> str:
    """Always use this tool to fetch actual live telemetry via REST API from SAP Integration Suite. It replaces intercept_sap_telemetry."""
    logger.info("📡 Tool invoked: Fetching live telemetry...")
    try:
        response = requests.get(f"{SAP_MOCK_BASE_URL}/telemetry", timeout=10)
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching telemetry: {str(e)}")
        # Provide fallback string representation if API fails for testing safety
        return json.dumps({"error": f"Failed to fetch telemetry: {str(e)}"})

@tool("Execute Remediation Payload")
def execute_remediation(payload_string: str) -> str:
    """
    Executes an action layer API call using an IDoc payload.
    Takes the structured JSON payload and passes it to the SAP execution layer.
    """
    logger.info("⚙️ Tool invoked: Executing remediation payload...")
    try:
        # Assuming payload parsing logic, parsing raw string returned by agent back to dict.
        # This could fail if agent provides markdown so we will try to clean it first.
        try:
            cleaned = payload_string.replace('```json', '').replace('```', '').strip()
            payload = json.loads(cleaned)
        except Exception as e:
            return json.dumps({"execute_status": "FAILED", "reason": "Invalid JSON format. You MUST regenerate successfully parseable JSON."})

        # Ensure we are passing exactly what the API expects without double nesting
        # Handling if the agent included the root 'payload' key vs if it just sent the inner object
        inner_payload = payload.get("payload", payload)

        response = requests.post(
            f"{SAP_MOCK_BASE_URL}/bapi/execute", 
            json={"bapi_name": "IDOC_INBOUND_ASYNCHRONOUS", "payload": inner_payload}, 
            timeout=10
        )
        
        if response.status_code == 200:
            return json.dumps({"execute_status": "SUCCESS", "response": response.json(), "api_code": 200})
            
        # 🔧 4. Add Retry Correction Logic (Triggers Agent Self-Correction)
        elif response.status_code == 422:
            return json.dumps({
                "execute_status": "RETRY_REQUIRED", 
                "reason": "422 Unprocessable Entity - Invalid SAP Schema. You MUST strictly regenerate the payload using the exact schema example provided in your prompt, including 'IDOCTYP', 'MESTYP', and 'E1EDK14' array."
            })
        elif response.status_code == 400:
            return json.dumps({
                "execute_status": "RETRY_REQUIRED", 
                "reason": f"API Validation Failed (HTTP 400): {response.text}. Correct your JSON string and retry."
            })
        else:
            return json.dumps({"execute_status": "FAILED", "reason": response.text, "api_code": response.status_code})

    except Exception as e:
        logger.error(f"Execution Error: {str(e)}")
        return json.dumps({"execute_status": "ERROR", "reason": str(e)})

