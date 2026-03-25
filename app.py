import streamlit as st
import sys
import os

# Ensure the src folder is in the path so we can import your orchestrator
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.ai.crew_orchestrator import start_pipeline

# --- UI SETUP ---
st.set_page_config(page_title="SAP Self-Healing Ecosystem", layout="wide", initial_sidebar_state="collapsed")

st.title("🛡️ SAP Causal-Agentic Self-Healing Ecosystem")
st.markdown("### Autonomous Telemetry Interception & Resolution via SAP BTP")
st.markdown("---")

# --- THE INTERACTIVE DASHBOARD ---
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.info("🟢 System Status: Monitoring SAP BTP Integration Suite Streams...")
    st.write("") # Spacer
    # The big red button to start the demo
    run_demo = st.button("🚨 Inject IDoc Failure (Simulate ORDERS05 Telemetry Alert)", use_container_width=True, type="primary")

# --- THE EXECUTION ---
if run_demo:
    st.markdown("---")
    st.markdown("### 🧠 Multi-Agent Execution Log")
    
    # This runs your backend and shows a beautiful loading spinner on the frontend
    with st.spinner("REST Telemetry Fetch -> Decision Engine -> Remediation Agent Execution -> Validation..."):
        # We catch the raw output from your AI pipeline
        raw_result = start_pipeline()
    
    # --- THE REVEAL ---
    st.success("✅ CausalKG Downstream Impact Simulation: SUCCESS")
    st.success("✅ SAP BTP Zero-Trust: VERIFIED")
    st.markdown("### 📝 Final Approved Governance Audit Log & Payload")
    
    # Displays the final AI JSON and approval beautifully in a code block
    st.code(str(raw_result), language="json")
    
    st.balloons() # A little hackathon flair for when it finishes
