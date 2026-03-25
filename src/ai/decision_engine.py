import json
import logging

logger = logging.getLogger("SAP_Decision")

from langchain_groq import ChatGroq
import os

def analyze_telemetry_and_decide(telemetry_json: str):
    """
    True Agent Autonomy: Triage System using LLM.
    Evaluates raw telemetry to intelligently decide strategy: ROUTE_TO_AUTONOMY, ESCALATE, or IGNORE.
    """
    logger.info("Intelligent Decision Engine parsing telemetry...")
    try:
        data = json.loads(telemetry_json)
        
        # Initialize Triage LLM
        llm = ChatGroq(
            temperature=0, 
            groq_api_key=os.environ.get("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant" 
        )
        
        prompt = f"""
        You are the SAP Operations Triage Manager.
        Analyze the following telemetry: {telemetry_json}
        
        Rules:
        1. If it is an IDoc Failure like ORDERS05 missing EKORG/VKORG, decide 'ROUTE_TO_AUTONOMY'.
        2. If it is a critical system database crash, decide 'ESCALATE'.
        3. If it is a minor warning, decide 'IGNORE'.
        
        Respond ONLY with one of the three decision words. Do not explain.
        """
        
        decision = llm.invoke(prompt).content.strip()
        logger.warning(f"Intelligent Triage Decision: {decision}")
        
        if "ROUTE_TO_AUTONOMY" in decision:
             return True, "Agent determined issue can be self-healed. Routing to Action Crew."
        else:
             return False, f"Agent determined manual escalation boundary: {decision}"
             
    except Exception as e:
         logger.error(f"Decision engine failed: {str(e)}")
         return False, "Telemetry parse error - Escalate"
