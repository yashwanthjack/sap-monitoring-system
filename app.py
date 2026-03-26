import streamlit as st

st.set_page_config(page_title="SAP Self-Healing Ecosystem", layout="wide")

st.title("🛡️ SAP Autonomous Self-Healing Ecosystem has been upgraded!")
st.warning("The UI has been migrated to a Real-Time WebSocket Interface for Enterprise Monitoring.")
st.markdown("### 🚀 How to launch the new Live Dashboard:")
st.code("uvicorn src.api.server:app --reload", language="bash")
st.markdown("Then visit **http://localhost:8000** in your browser.")
