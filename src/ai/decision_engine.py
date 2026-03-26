import json
import logging
from langchain_groq import ChatGroq
import os

logger = logging.getLogger("SAP_Decision")

def analyze_telemetry_and_decide(telemetry_json: str):
    """
    True Agent Autonomy: Triage System using LLM with Confidence Scoring
    Evaluates raw telemetry and outputs structured decision.
    """
    logger.info("Intelligent Decision Engine parsing telemetry...")
    try:
        # Check if lists are passed (Multi-IDoc)
        data = json.loads(telemetry_json)
        if isinstance(data, list):
            logger.info(f"Handling multiple IDoc errors: count={len(data)}")
        
        llm = ChatGroq(
            temperature=0, 
            groq_api_key=os.environ.get("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant" 
        )
        
        prompt = f"""
        You are the SAP Operations Triage Manager.
        Analyze the following telemetry (which could be a single error or an array of multiple errors): {telemetry_json}
        
        Rules:
        1. Identify the errors. If it's an IDoc Failure like missing EKORG/VKORG or similar structural issues, decide 'ROUTE_TO_AUTONOMY'.
        2. If it is a critical system database crash or an unknown anomaly, decide 'ESCALATE'.
        3. If it is a minor warning, decide 'IGNORE'.
        4. Provide a confidence_score between 0.0 and 1.0. If the error is standard and deterministic (like IDoc missing mappings), score > 0.8.
        5. Describe a brief 'strategy'.
        
        You MUST respond with valid JSON ONLY. No markdown, no explanations outside JSON.
        Format:
        {{
            "decision": "ROUTE_TO_AUTONOMY" | "ESCALATE" | "IGNORE",
            "confidence_score": 0.95,
            "strategy": "Inject correct EKORG segment and resubmit via BAPI",
            "target": "ORDERS05"
        }}
        """
        
        raw_output = llm.invoke(prompt).content.strip()
        # Clean potential markdown
        cleaned = raw_output.replace('```json', '').replace('```', '').strip()
        decision_obj = json.loads(cleaned)
        
        logger.warning(f"Intelligent Triage Decision: {decision_obj}")
        
        decision = decision_obj.get("decision", "ESCALATE")
        confidence = decision_obj.get("confidence_score", 0.0)
        strategy = decision_obj.get("strategy", "None")
        
        if confidence < 0.7:
             return False, f"Confidence too low ({confidence}). Escalating. Strategy proposed: {strategy}"
        
        if decision == "ROUTE_TO_AUTONOMY":
             return True, f"Agent determined self-heal with {confidence*100}% confidence. Strategy: {strategy}"
        else:
             return False, f"Agent determined manual escalation boundary: {decision}"
             
    except Exception as e:
         logger.error(f"Decision engine failed: {str(e)}")
         return False, "Telemetry parse error - Escalate"
