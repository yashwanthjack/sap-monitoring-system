"""
SAP Self-Healing MVP — Streamlit Demo Dashboard
Atos Srijan Hackathon Command Center

This dashboard provides a visual interface for the 3-Agent Self-Healing Pipeline.
It can run the pipeline directly (without FastAPI) for simplicity.
"""

import streamlit as st
import sys
import os
import json
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ai.crew_orchestrator import run_self_healing_pipeline
from src.monitor.log_reader import get_all_scenarios, SAP_ERROR_SCENARIOS
from src.knowledge.graph import causal_kg
from src.execution.sap_simulator import get_db_state, reset_db
from src.ai.audit_logger import get_audit_log, clear_audit_log

# ─── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAP Self-Healing | Atos Srijan",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0a1628 0%, #1a2744 50%, #0d3b66 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #60a5fa;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin: 0.3rem 0 0 0;
    }

    .agent-card {
        background: linear-gradient(145deg, #0f1923 0%, #162033 100%);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    .agent-card:hover {
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 6px 24px rgba(59, 130, 246, 0.15);
    }
    .agent-card h3 {
        color: #60a5fa;
        font-size: 1.05rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
    }
    .agent-card p {
        color: #cbd5e1;
        font-size: 0.85rem;
        margin: 0.2rem 0;
        line-height: 1.5;
    }

    .status-resolved {
        background: linear-gradient(135deg, #064e3b, #065f46);
        color: #34d399;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.1rem;
        text-align: center;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .status-failed {
        background: linear-gradient(135deg, #7f1d1d, #991b1b);
        color: #fca5a5;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.1rem;
        text-align: center;
        border: 1px solid rgba(252, 165, 165, 0.3);
    }

    .metric-box {
        background: linear-gradient(145deg, #0f1923 0%, #1a2744 100%);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-box h4 { color: #94a3b8; font-size: 0.75rem; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-box .value { color: #60a5fa; font-size: 1.6rem; font-weight: 700; margin: 0.3rem 0 0 0; }

    .stButton > button {
        background: linear-gradient(135deg, #1e40af, #3b82f6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #60a5fa) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #111827 100%);
    }
    div[data-testid="stSidebar"] h1, div[data-testid="stSidebar"] h2,
    div[data-testid="stSidebar"] h3 { color: #60a5fa; }

    .causal-chain {
        background: #0d1b2a;
        border-left: 4px solid #f59e0b;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #fbbf24;
        font-family: 'Consolas', monospace;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🛡️ Causal-Agentic Self-Healing SAP Ecosystem</h1>
    <p>Multi-Agent Orchestration • Causal Knowledge Graph • Autonomous Remediation • Governance Audit</p>
</div>
""", unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 Control Panel")

    st.markdown("---")
    st.markdown("#### 📋 Error Scenario")
    scenarios = get_all_scenarios()
    scenario_labels = [f"{s['type']}/{s['subtype']} ({s['severity']})" for s in scenarios]
    selected_idx = st.selectbox(
        "Select SAP Error to Inject",
        options=range(len(scenarios)),
        format_func=lambda i: scenario_labels[i],
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        run_btn = st.button("🚀 Run Pipeline", use_container_width=True)
    with col2:
        reset_btn = st.button("🔄 Reset System", use_container_width=True)

    if reset_btn:
        reset_db()
        clear_audit_log()
        st.success("System reset complete!")

    st.markdown("---")
    st.markdown("#### 🏗️ Architecture")
    st.markdown("""
    ```
    SAP Logs (Simulated)
         ↓
    Agent 1: Diagnostic
         ↓
    Agent 2: Causal Planner
         ↓
    Agent 3: Remediation
         ↓
    Audit Log + DB Update
    ```
    """)

    st.markdown("---")
    st.markdown("#### 🛠️ Tech Stack")
    st.caption("Python • CrewAI • NetworkX • SQLite • FastAPI • Streamlit")


# ─── Main Content ────────────────────────────────────────────────────

if run_btn:
    # ── Show pipeline execution with animated steps ───────────────
    st.markdown("---")
    st.markdown("## 🔄 Pipeline Execution")

    progress_bar = st.progress(0, text="Initializing self-healing pipeline...")

    # Step 1: Show the injected error
    with st.container():
        scenario = SAP_ERROR_SCENARIOS[selected_idx]
        st.markdown(f"""
        <div class="agent-card">
            <h3>📡 SAP Error Intercepted</h3>
            <p><strong>Type:</strong> {scenario['type']} / {scenario['subtype']}</p>
            <p><strong>System:</strong> {scenario['system']}</p>
            <p><strong>Severity:</strong> {scenario['severity']}</p>
            <p><strong>Raw Log:</strong></p>
            <p style="color: #f87171; font-family: Consolas, monospace; font-size: 0.8rem;
               background: rgba(248, 113, 113, 0.1); padding: 0.5rem; border-radius: 6px;">
               {scenario['raw_log']}</p>
        </div>
        """, unsafe_allow_html=True)

    progress_bar.progress(15, text="⚡ Invoking Diagnostic Agent...")
    time.sleep(0.8)

    # Run the pipeline
    result = run_self_healing_pipeline(scenario_index=selected_idx)
    steps = result.get("steps", [])

    # Step 2: Diagnostic Agent result
    progress_bar.progress(40, text="🔍 Diagnostic Agent analyzing root cause...")
    time.sleep(0.5)

    if len(steps) >= 1:
        s = steps[0]
        st.markdown(f"""
        <div class="agent-card">
            <h3>🔍 Agent 1 — Diagnostic Agent</h3>
            <p><strong>Action:</strong> {s['action']}</p>
            <p><strong>Human-Readable Translation:</strong></p>
            <p style="color: #34d399;">{s['output'].get('human_readable', 'N/A')}</p>
            <p><strong>Root Cause Identified:</strong> <span style="color: #fbbf24;">{s['output'].get('root_cause', 'N/A')}</span></p>
            <p><strong>Severity:</strong> {s['output'].get('severity', 'N/A')}</p>
            <p style="color: #4ade80; font-weight: 600;">{s['status']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Step 3: Causal Planner result
    progress_bar.progress(65, text="🧠 Causal Planning Agent querying Knowledge Graph...")
    time.sleep(0.5)

    if len(steps) >= 2:
        s = steps[1]
        chains = result.get("plan", {}).get("causal_chain", [])
        chain_html = ""
        for chain in chains:
            chain_html += f'<div class="causal-chain">⛓️ {chain}</div>'

        st.markdown(f"""
        <div class="agent-card">
            <h3>🧠 Agent 2 — Causal Planning Agent</h3>
            <p><strong>Action:</strong> {s['action']}</p>
            <p><strong>Recommended Fix:</strong> <span style="color: #60a5fa; font-weight: 600;">{s['output'].get('fix', 'N/A')}</span></p>
            <p><strong>Downstream Impact:</strong> {s['output'].get('downstream_impact_count', 0)} entities affected</p>
            <p><strong>Verified by Knowledge Graph:</strong> {'✅ Yes' if s['output'].get('verified_by_kg') else '❌ No'}</p>
            <p><strong>Causal Chain:</strong></p>
            {chain_html}
            <p style="color: #4ade80; font-weight: 600;">{s['status']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Step 4: Remediation result
    progress_bar.progress(90, text="🛡️ Remediation Agent executing BAPI payload...")
    time.sleep(0.5)

    if len(steps) >= 3:
        s = steps[2]
        st.markdown(f"""
        <div class="agent-card">
            <h3>🛡️ Agent 3 — Remediation & Governance Agent</h3>
            <p><strong>Action:</strong> {s['action']}</p>
            <p><strong>Governance Check:</strong> {'✅ PASSED' if s['output'].get('governance_check') == 'PASSED' else '❌ FAILED'}</p>
            <p><strong>BAPI Result:</strong> <span style="color: #c084fc;">{s['output'].get('bapi_result', 'N/A')}</span></p>
            <p><strong>Resolved:</strong> {'✅ Yes' if s['output'].get('resolved') else '❌ No'}</p>
            <p style="color: #4ade80; font-weight: 600;">{s['status']}</p>
        </div>
        """, unsafe_allow_html=True)

    progress_bar.progress(100, text="Pipeline complete!")

    # Final status
    resolved = result.get("resolved", False)
    if resolved:
        st.markdown(f'<div class="status-resolved">✅ SELF-HEALING SUCCESSFUL — Error Automatically Resolved</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-failed">❌ SELF-HEALING INCOMPLETE — Manual Intervention Required</div>',
                    unsafe_allow_html=True)

    st.markdown(f"> **Summary:** {result.get('summary', 'N/A')}")


# ─── Bottom Tabs ─────────────────────────────────────────────────────
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 SAP Database State", "📜 Audit Trail", "🕸️ Knowledge Graph"])

with tab1:
    db_state = get_db_state()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Materials (MARA)")
        if db_state.get("materials"):
            st.dataframe(db_state["materials"], use_container_width=True, hide_index=True)
        else:
            st.info("No materials in the system.")

    with col2:
        st.markdown("#### Vendors (LFA1)")
        if db_state.get("vendors"):
            st.dataframe(db_state["vendors"], use_container_width=True, hide_index=True)
        else:
            st.info("No vendors in the system.")

with tab2:
    audit = get_audit_log(limit=30)
    if audit:
        st.dataframe(audit, use_container_width=True, hide_index=True)
    else:
        st.info("No audit log entries yet. Run the pipeline to generate entries.")

with tab3:
    graph_data = causal_kg.get_graph_data()
    st.markdown("#### Causal Knowledge Graph — RDF-like Triples")

    # Display edges as a table
    if graph_data.get("edges"):
        edges_display = []
        for edge in graph_data["edges"]:
            icon = "🔴" if edge["relation"] == "causes" else "🟢"
            edges_display.append({
                "": icon,
                "Source": edge["source"],
                "Relation": edge["relation"].upper(),
                "Target": edge["target"],
                "Description": edge["description"][:80],
            })
        st.dataframe(edges_display, use_container_width=True, hide_index=True)
    else:
        st.info("Knowledge graph is empty.")

    st.markdown(f"**Total Nodes:** {len(graph_data.get('nodes', []))} | "
                f"**Total Edges:** {len(graph_data.get('edges', []))}")
