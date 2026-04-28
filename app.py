import streamlit as st
from agent.reservoir_agent import ReservoirAgent
import pandas as pd
import io
import time
import plotly.express as px
import numpy as np
import time
from datetime import datetime, timedelta
import os
import sys
from streamlit_option_menu import option_menu
import streamlit_shadcn_ui as ui
from agent.utils.reservoir_math import generate_corey_relperm, calculate_eur
from agent.utils.reservoir_math_fit import fit_production_data
import json
import matplotlib.pyplot as plt
import numpy as np

# Ensure the project root is in the search path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)



# --- FALLBACK DATASET ---
def load_fallback_data():
    dates = pd.date_range(start="2020-01-01", periods=12, freq='ME')
    return pd.DataFrame({
        'Date': dates,
        'Oil_Production_BOPD': [5000, 4800, 4700, 4550, 4400, 4200, 4100, 3950, 3800, 3700, 3600, 3500],
        'Water_Cut_Pct': [2, 3, 5, 8, 12, 15, 18, 22, 25, 29, 33, 38],
        'Pressure_PSI': [3200, 3180, 3150, 3120, 3100, 3050, 3000, 2950, 2900, 2850, 2800, 2750]
    })

st.set_page_config(page_title="Exzing Reservoir Agent", layout="wide")

def check_rate_limit():
    """Prevents brute-force testing: max 10 requests per minute."""
    if 'request_history' not in st.session_state:
        st.session_state.request_history = []
    
    now = datetime.now()
    # Filter history to only include last 60 seconds
    st.session_state.request_history = [t for t in st.session_state.request_history if now - t < timedelta(minutes=1)]
    
    if len(st.session_state.request_history) >= 10:
        return False
    
    st.session_state.request_history.append(now)
    return True

import re

def format_ai_table(text):
    """Cleans up AI-generated markdown tables for professional display."""
    if not isinstance(text, str):
        return text
    # 1. Replace HTML line breaks with a space or a standard Markdown bullet
    text = text.replace("<br>", " ")
    # 2. Ensure tables have proper spacing around pipes
    text = re.sub(r'(\|[^\n]+\|)', lambda m: m.group(0).replace('  ', ' '), text)
    return text

def render_industrial_chat(context_name, context_data, llm_choice):
    # 1. Unique key for this tab's history
    msg_key = f"{context_name}_messages"
    if msg_key not in st.session_state:
        st.session_state[msg_key] = []

    chat_history = st.session_state[msg_key]

    # 2. Display existing history with Strategy 3 (Auto-Collapse)
    if chat_history:
        st.write(f"--- {context_name.title()} Discussion Thread ---")
        with st.container(height=450, border=True):
            total = len(chat_history)
            for i, msg in enumerate(chat_history):
                if i < total - 2:
                    with st.expander(f"📜 Previous Step: {msg['role'].capitalize()}"):
                        st.markdown(msg["content"])
                else:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

    # 3. THE FOLLOW-UP LOGIC
    # st.chat_input is the trigger. It allows the user to type infinitely.
    if prompt := st.chat_input(f"Ask a follow-up about {context_name}...", key=f"in_{context_name}"):
        
        # Add user's new question to the list
        chat_history.append({"role": "engineer", "content": prompt})
        
        with st.spinner("Consultant is reviewing the thread..."):
            # Construct a "Memory Prompt"
            # We take the last 3 messages to give the AI immediate conversational context
            recent_history = ""
            for m in chat_history[-4:-1]: # Last few exchanges before this new prompt
                recent_history += f"{m['role'].upper()}: {m['content']}\n"

            full_payload = f"""
            TECHNICAL CONTEXT:
            {context_data}
            
            PREVIOUS CONVERSATION:
            {recent_history}
            
            NEW FOLLOW-UP QUESTION:
            {prompt}
            """
            
            # Call the LLM Engine
            response = st.session_state.agent.engine.analyze_reservoir_task(
                llm_choice, 
                f"You are a Senior {context_name} Expert. Use the technical context and conversation history to provide a precise follow-up.", 
                full_payload
            )
            
            # Add AI's answer to history
            chat_history.append({"role": "Consultant", "content": response})
            
            # Refresh the UI to show the new messages
            st.rerun()

if 'agent' not in st.session_state:
    st.session_state.agent = ReservoirAgent()
    
# Persistent Audit Log (In Session State, pointing toward SQL)
if 'audit_trail' not in st.session_state:
    st.session_state.audit_trail = []


# This will be: .../reservoir_mgt_agent/app.py/
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Define Absolute Paths pointing to the 'data' subfolder inside 'agent'
path_logo = os.path.join(current_dir, 'assets', 'favicon.png')
st.set_page_config(page_title="Exzing Reservoir Agent", page_icon=path_logo, layout="wide")    


    

# --- INDUSTRIAL UI ENHANCEMENTS ---
st.markdown("""
    <style>
    /* 1. Global Font and Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #fcfcfc;
    }
    
    /* Sticky Top Navbar Container */
    .nav-container {
        position: fixed;
        top: 0;
        width: 100%;
        z-index: 99;
    }

    /* Atlas Gradient Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #FEAC5E, #C779D0, #4BC0C8) !important;
        border-right: 1px solid rgba(0,0,0,0.1);
    }
    
    /* Sidebar Text Legibility */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #red !important;
        text-shadow: 0px 1px 2px rgba(0,0,0,0.2);
    }
    
    

    /* 2. Command Center Sidebar */
    [data-testid="stSidebar"] {
        background: #FEAC5E !important; /* Fallback */
        background: linear-gradient(to bottom, #FEAC5E, #cbdcee, #cbdcee) !important;
        border-right: 1px solid #e0e0e0;
    }
    [data-testid="stSidebar"] .nav-link { color: white !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 600;
    }

    /* 3. Metrics / KPI Cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #eef0f2;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] {
        color: #6c757d !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        color: #0078d4 !important; /* Azure Blue */
        font-weight: 700 !important;
    }

    /* 4. Professional Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #fcfcfc;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #495057;
        font-weight: 400;
    }
    .stTabs [aria-selected="true"] {
        color: #0078d4 !important;
        border-bottom: 2px solid #0078d4 !important;
        font-weight: 600 !important;
    }

    /* 5. Industrial Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 3em;
        background-color: #0078d4;
        color: white;
        border: none;
        transition: all 0.3s ease;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        background-color: #005a9e;
        box-shadow: 0 4px 12px rgba(0, 120, 212, 0.3);
    }

    /* 6. Clean Data Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #eef0f2;
        border-radius: 8px;
    }

    /* 7. Warnings and Success */
    .stAlert {
        border-radius: 6px;
        border: none;
    }
    
    /* Ensure tables and text wrap inside the scrollable container */
    [data-testid="stVVerticalBlock"] div[style*="height"] {
        background-color: #ffffff;
    }
    
    .stMarkdown table {
        display: block;
        width: 100% !important;
        overflow-x: auto; /* Adds horizontal scroll if table is too wide */
        word-wrap: break-word;
    }

    /* Professional scrollbar styling (Modern Look) */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e0;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #0078d4;
    }
    
    </style>
    """, unsafe_allow_html=True)    
    

st.title("Subsurface Intelligence Agent")
st.subheader("Frontier Reservoir Consultant")


# Custom CSS to hide the deploy button
st.markdown(
    """
    <style>
    .stAppDeployButton {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 3. PROFESSIONAL HORIZONTAL NAVBAR ---
# This is the "ecoapp.page" style menu
selected_workspace = option_menu(
    menu_title=None, 
    options=["Simulator Debugger", "Asset Intelligence", "RelPerm Generator", "Governance & Audit", "User Guide"],
    icons=["tools", "graph-up", "droplet-half", "shield-lock"], 
    menu_icon="cast", 
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#ffffff", "border-radius": "0", "box-shadow": "0 2px 10px rgba(0,0,0,0.05)"},
        "icon": {"color": "#0078d4", "font-size": "18px"}, 
        "nav-link": {"font-size": "14px", "text-align": "center", "margin":"5px", "--hover-color": "#f0f2f6", "text-transform": "uppercase", "letter-spacing": "1px"},
        "nav-link-selected": {"background-color": "#0078d4", "font-weight": "600"},
    }
)

with st.sidebar:
    #st.header("Data Ingestion")
    #uploaded_file = st.file_uploader("Upload Subsurface Data (CSV/XLSX)", type=["csv", "xlsx"])
    llm_choice = st.selectbox("Reasoning Engine:", ["GROQ", "AZURE"], help="AZURE: High-compliance GPT-5-main. GROQ: openai/gpt-oss-120b High-speed technical reasoning.")
    
    with st.expander("🛡️ Security & Privacy Compliance Information"):
        st.info("""
        **Exzing Zero-Data Retention (ZDR) Policy:**
        1. **No Training:** Your proprietary reservoir descriptions are processed via Azure OpenAI 'No-Training' endpoints.
        2. **In-Memory Only:** Input data is handled in volatile memory and purged after the session expires.
        3. **Adversarial Shield:** Rate limiting is active to prevent brute-force probing of engineering logic.
        4. **Encryption:** All data in transit is protected by TLS 1.2+ within the North Central US Azure region.
        5. **Model's Security:** Models are secured with Azure Key Vault.
        6. **Governance Status:** AI Content Safety Active.
        """)
        st.sidebar.caption("© 2026 Exzing Technology Ltd")     
        st.image(path_logo, use_container_width=True)

# --- Initialize Debugger Chat History ---
if "debugger_chat" not in st.session_state:
    st.session_state.debugger_chat = []

if selected_workspace == "Simulator Debugger":
    st.header("🛠️ Professional Simulator Debugger")
    st.info("Diagnose crashes and iterate on technical fixes through an interactive consultant session.")
    
    # 1. INPUT AREA
    col1, col2 = st.columns(2)
    with col1:
        deck_snippet = st.text_area("1. Paste .DATA Snippet:", height=200, key="dsnip")
    with col2:
        error_log = st.text_area("2. Paste Error Log:", placeholder="Paste error logs from ECLIPSE/OPM...", height=200, key="errlog")
    
    # 2. INITIAL TRIGGER
    if st.button("Run Technical Diagnosis", type="primary"):
        if deck_snippet and error_log:        
            with st.spinner(f"Architecting fix via {llm_choice}..."):
                # Call existing logic
                report = st.session_state.agent.generate_diagnostic_report(deck_snippet, llm_choice, error_log)
                
                # Clear previous chat and start a new one with the AI's report
                st.session_state.debugger_chat = [
                    {"role": "Consultant", "content": report['deck'], "score": report['safety_score']}
                ]
                
                # Log to Global Audit Trail
                st.session_state.audit_trail.append({
                    "Timestamp": report.get('timestamp', 'N/A'),
                    "Action": "Pro Debugger Initialized",
                    "Safety_Score": report['safety_score'],
                    "Provider": llm_choice
                })
        else:
            st.warning("Please provide both a deck snippet and an error log to begin.")

    # 3. CONVERSATIONAL INTERFACE
    if st.session_state.debugger_chat:
        st.divider()
        st.subheader("💬 Technical Consultation Thread")
        
        # Wrap the chat in a scrollable container to keep UI clean
        with st.container(height=500, border=True):
            total_messages = len(st.session_state.debugger_chat)
            
            for i, msg in enumerate(st.session_state.debugger_chat):
                # If it's an old message (not the last two), wrap it in an expander
                if i < total_messages - 2:
                    with st.expander(f"📜 View Previous Step: {msg['role'].capitalize()}"):
                        st.markdown(msg["content"])
                else:
                    # Show the most recent exchanges in full
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                    if "score" in msg:
                        st.caption(f"Technical Integrity Score: {msg['score']}%")

        # 4. FOLLOW-UP INPUT (The 'Two-Way' Part)
        if prompt := st.chat_input("Ask a follow-up question about this fix..."):
            # Display user message
            st.session_state.debugger_chat.append({"role": "engineer", "content": prompt})
            
            # Generate follow-up using the full context
            with st.spinner("Consultant is thinking..."):
                # We feed the AI the original deck and log + the new question
                full_context_prompt = f"""
                ORIGINAL DECK: {deck_snippet}
                ORIGINAL ERROR: {error_log}
                PREVIOUS ANALYSIS: {st.session_state.debugger_chat[-2]['content'] if len(st.session_state.debugger_chat)>1 else ""}
                USER FOLLOW-UP: {prompt}
                """
                
                follow_up_response = st.session_state.agent.engine.analyze_reservoir_task(
                    llm_choice, 
                    "You are a Senior Reservoir Simulation Consultant. Answer follow-up technical questions based on the provided context.", 
                    full_context_prompt
                )
                
                st.session_state.debugger_chat.append({"role": "Consultant", "content": follow_up_response})
                st.rerun()

        
        # 5. HUMAN-IN-THE-LOOP & EXPORT
        st.divider()
        latest_res = st.session_state.debugger_chat[-1]["content"]
        
        st.info("💡 **HITL Required:** Verify the latest technical advice before application.")
        reviewed = st.checkbox("I verify the suggested remediation.", key="chat_hitl")
        
        if reviewed:
            st.download_button(
                label="📥 Export Current Fix (.TXT)",
                data=latest_res,
                file_name=f"Exzing_Fix_Iterative.txt",
                mime="text/plain"
            )
    
elif selected_workspace == "Asset Intelligence":
    st.header("📈 Asset Intelligence Dashboard")
    st.info("Bulk Decline Curve Analysis (DCA) and Estimated Ultimate Recovery (EUR) tool.")

    # ── 1. DATA INPUT ────────────────────────────────────────────────────────
    # Single canonical format: Field, WellName, Date, OilRate
    # Placeholder matches this exactly — no format switching.
    st.subheader("Data Source")

    REQUIRED_COLS = ["Field", "WellName", "Date", "OilRate"]
    
    def _reset_asset_outputs():
        for key in [
            "last_diagnostic",
            "asset_intel_hitl",
            "asset_intel_selected_wells",
            "asset_intel_scatter_x",
            "asset_intel_scatter_y",
        ]:
            st.session_state.pop(key, None)

    data_source = st.radio(
        "Choose input method:",
        ["Upload production CSV", "Use placeholder dataset"],
        horizontal=True,
        key="asset_intel_data_source",
        on_change=_reset_asset_outputs,
    )  


    df = None

    if data_source == "Upload production CSV":
        uploaded_file = st.file_uploader(
            f"Upload CSV with columns: {', '.join(REQUIRED_COLS)}",
            type="csv",
            key="asset_intel_uploader",
        )
        if uploaded_file:
            df = pd.read_csv(uploaded_file)

    else:
        st.info("Using built-in placeholder dataset (3 synthetic wells, 1 field).")
        # Matches REQUIRED_COLS exactly — same format as any uploaded CSV
        _t = np.arange(24)
        df = pd.DataFrame({
            "Field":    ["DEMO-FIELD"] * 72,
            "WellName": ["WELL-A"] * 24 + ["WELL-B"] * 24 + ["WELL-C"] * 24,
            "Date":     pd.date_range("2022-01-01", periods=24, freq="MS").tolist() * 3,
            "OilRate":  (
                # WELL-A: exponential (b≈0) — boundary-dominated conventional
                [round(4500 * np.exp(-0.10 * i), 1) for i in _t] +
                # WELL-B: hyperbolic (b=0.8) — layered / partial pressure support
                [round(3200 / (1 + 0.8 * 0.15 * i) ** (1 / 0.8), 1) for i in _t] +
                # WELL-C: b=1.2 — transient/fractured; deliberately triggers b>1 flag
                [round(2800 / (1 + 1.2 * 0.10 * i) ** (1 / 1.2), 1) for i in _t]
            ),
        })
        with st.expander("Preview placeholder data"):
            st.dataframe(df, use_container_width=True)

    # ── 2. EMPTY STATE ───────────────────────────────────────────────────────
    if df is None:
        st.markdown(
            """
            <div style="text-align:center; padding:50px;">
                <h2 style="color:#adb5bd;">Awaiting Asset Configuration</h2>
                <p style="color:#ced4da;">Upload your production CSV or select the placeholder above.</p>
                <img src="https://cdn-icons-png.flaticon.com/512/3090/3090011.png"
                     width="100" style="opacity:0.15;">
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── 3. VALIDATE & PARSE ──────────────────────────────────────────────────
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        st.error(
            f"CSV is missing required columns: **{', '.join(missing)}**. "
            f"Expected: {', '.join(REQUIRED_COLS)}"
        )
        st.stop()

    df["Date"]    = pd.to_datetime(df["Date"], errors="coerce")
    df["OilRate"] = pd.to_numeric(df["OilRate"], errors="coerce")

    invalid_rates = df["OilRate"].isna().sum()
    if invalid_rates:
        st.warning(f"{invalid_rates} rows with unparseable OilRate values dropped.")
        df = df.dropna(subset=["OilRate"])

    fields = df["Field"].unique()
    wells  = df["WellName"].unique()
    st.write(f"Detected **{len(fields)} field(s)** and **{len(wells)} wells**.")

    # ── 4. PARAMETERS (all controls together, before computation) ────────────
    st.subheader("Parameters")
    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        econ_limit = st.number_input(
            "Economic Limit (STB/D)",
            min_value=1.0, value=50.0, step=5.0,
            key="asset_intel_econ_limit",
            help=(
                "Terminal rate below which a well is uneconomic. "
                "SPE-PRMS §3.4 defines EUR as cumulative production down "
                "to this point of zero net cash flow."
            ),
        )
    with col_p2:
        abandonment_buffer = st.slider(
            "Abandonment warning buffer (×)",
            min_value=1.1, max_value=3.0, value=1.5, step=0.1,
            key="asset_intel_abandonment_buffer",
            help=(
                "Flag wells whose current rate is within this multiple of the "
                "economic limit. 1.5× at Di=10%/month gives ~4 months lead "
                "time for workover or P&A decisions. Adjust for your "
                "operational lead time and field economics."
            ),
        )
    with col_p3:
        forecast_horizon_years = st.slider(
            "Max forecast horizon (years)",
            min_value=5, max_value=50, value=20, step=5,
            key="asset_intel_forecast_horizon",
            help=(
                "SPE-PRMS (2018) §3.4 requires forecasting to the economic "
                "limit, not a fixed calendar date. This cap prevents runaway "
                "tails on high b-factor wells (b > 1) common in tight/shale "
                "reservoirs where transient flow can persist for decades. "
                "Typical ranges: conventional onshore 15–25 yr, "
                "deepwater 10–20 yr, unconventional 30–50 yr."
            ),
        )

    # ── 5. DCA COMPUTATION LOOP ──────────────────────────────────────────────
    results     = []
    agent_flags = []

    for well in wells:
        well_data    = df[df["WellName"] == well].sort_values("Date")
        rates        = well_data["OilRate"].tolist()
        field        = well_data["Field"].iloc[0]

        if len(rates) < 3:
            st.warning(f"Skipping {well} — fewer than 3 data points.")
            continue

        try:
            qi, di, b = fit_production_data(rates)
        except Exception as e:
            st.warning(f"DCA fit failed for {well}: {e}. Using fallback parameters.")
            qi, di, b = rates[0], 0.125, 1.0

        eur_val, life_yrs = calculate_eur(qi, di, b, econ_limit)
        current_rate      = rates[-1]
        remaining_life    = (eur_val - sum(rates) / 365) / max(current_rate, 1e-9)

        results.append({
            "Field":                field,
            "Well":                 well,
            "Current Rate (STB/D)": round(current_rate, 1),
            "qi (STB/D)":           round(qi, 1),
            "Di (%/yr)":            round(di * 100, 2),
            "b-factor":             round(b, 3),
            "EUR (MMSTB)":          round(eur_val / 1e6, 3),
            "Field Life (Yrs)":     life_yrs,
            "Remaining Life (Yrs)": round(max(remaining_life, 0), 1),
        })

        # Anomaly flags — fed verbatim to the agent prompt
        if b > 1.0:
            agent_flags.append(
                f"⚠️ **{well}** ({field}): b = {b:.3f} > 1.0 — transient flow, "
                f"natural fractures, or pressure support. Recommend aquifer/pressure review."
            )
        if current_rate < econ_limit * abandonment_buffer:
            buffer_pct     = (abandonment_buffer - 1) * 100
            di_frac        = di / 100   # convert stored %/yr back to fraction for formula
            months_to_econ = (
                np.log(current_rate / econ_limit) / max(di_frac, 1e-6)
                if b < 0.01
                else (((current_rate / econ_limit) ** (-b) - 1) / (b * max(di_frac, 1e-6)))
            )
            agent_flags.append(
                f"🔴 **{well}** ({field}): Rate {current_rate:.0f} STB/D is within "
                f"{buffer_pct:.0f}% of econ. limit ({econ_limit:.0f} STB/D). "
                f"≈ {max(months_to_econ, 0):.1f} months to abandonment. "
                f"Workover / P&A candidate."
            )
        if di * 100 > 30:
            agent_flags.append(
                f"📉 **{well}** ({field}): Decline {di * 100:.1f}%/yr exceeds 30% threshold. "
                f"Assess artificial lift or stimulation."
            )

    if not results:
        st.error("No wells could be processed. Check your CSV format and data quality.")
        st.stop()

    results_df = pd.DataFrame(results)

    # ── 6. FIELD-LEVEL ROLLUP ────────────────────────────────────────────────
    # Computed here — outside any expander — so agent prompt and export
    # can always access it regardless of which UI panels the user opens.
    field_summary = (
        results_df
        .groupby("Field")
        .agg(
            Wells           = ("Well",                 "count"),
            Total_EUR       = ("EUR (MMSTB)",          "sum"),
            Avg_EUR         = ("EUR (MMSTB)",          "mean"),
            Avg_qi          = ("qi (STB/D)",           "mean"),
            Avg_Di          = ("Di (%/yr)",            "mean"),
            Avg_b           = ("b-factor",             "mean"),
            Wells_Near_Econ = ("Current Rate (STB/D)",
                               lambda x: (x < econ_limit * abandonment_buffer).sum()),
        )
        .round(3)
        .reset_index()
        .rename(columns={
            "Total_EUR":       "Total EUR (MMSTB)",
            "Avg_EUR":         "Avg EUR/Well (MMSTB)",
            "Avg_qi":          "Avg qi (STB/D)",
            "Avg_Di":          "Avg Di (%/yr)",
            "Avg_b":           "Avg b-factor",
            "Wells_Near_Econ": "Wells Near Econ. Limit",
        })
        .sort_values("Total EUR (MMSTB)", ascending=False)
    )

    # ── 7. RESULTS TABLES ────────────────────────────────────────────────────
    st.subheader("Results")
    tab_well, tab_field = st.tabs(["Well Results", "Field Rollup"])

    with tab_well:
        st.dataframe(results_df, use_container_width=True)

    with tab_field:
        st.dataframe(field_summary, use_container_width=True)
        st.caption(
            "Total EUR = bottom-up sum of well EURs (SPE-PRMS §3.4). "
            "Does not account for facility capacity or shared infrastructure limits."
        )

    # ── 8. VISUALISATIONS ────────────────────────────────────────────────────
    st.subheader("Charts")

    MAX_DISPLAY    = 20
    all_well_names = results_df["Well"].tolist()

    with st.expander("Chart controls and visualization", expanded=True):
        ctrl_col1, ctrl_col2 = st.columns(2)

        with ctrl_col1:
            selected_wells = st.multiselect(
                "Wells to display (max 20)",
                options=all_well_names,
                default=all_well_names[:min(5, len(all_well_names))],
                key="asset_intel_selected_wells",
                help=(
                    "Showing all wells on one chart is unreadable at scale. "
                    "Use the Field Rollup tab for portfolio-level EUR. "
                    "Select individual wells here for forecast and risk charts."
                ),
            )
            if len(selected_wells) > MAX_DISPLAY:
                st.warning(f"Capped at {MAX_DISPLAY} wells for readability.")
                selected_wells = selected_wells[:MAX_DISPLAY]

        with ctrl_col2:
            scatter_x = st.selectbox(
                "Scatter X-axis",
                options=["Di (%/yr)", "qi (STB/D)", "EUR (MMSTB)", "Remaining Life (Yrs)"],
                index=0,
                key="asset_intel_scatter_x",
                help="Horizontal axis for the decline risk scatter chart.",
            )
            scatter_y = st.selectbox(
                "Scatter Y-axis",
                options=["b-factor", "EUR (MMSTB)", "Remaining Life (Yrs)", "Di (%/yr)"],
                index=0,
                key="asset_intel_scatter_y",
                help="Vertical axis for the decline risk scatter chart.",
            )

        plot_df = results_df[results_df["Well"].isin(selected_wells)]

        # Chart 1 — EUR by field (always all fields) + per-well for selected wells
        st.markdown("#### EUR Summary")
        fig_eur, axes = plt.subplots(1, 2, figsize=(13, max(3.5, len(fields) * 0.6)))

        axes[0].barh(field_summary["Field"], field_summary["Total EUR (MMSTB)"],
                     color="#2196F3", edgecolor="white")
        axes[0].axvline(
            field_summary["Total EUR (MMSTB)"].mean(),
            color="#FF5722", linestyle="--", linewidth=1.2, label="Portfolio avg",
        )
        axes[0].set_xlabel("Total EUR (MMSTB)")
        axes[0].set_title("By Field (all)")
        axes[0].invert_yaxis()
        axes[0].legend(fontsize=8)

        field_color_map = {
            f: plt.cm.tab10(i / max(len(fields), 1))
            for i, f in enumerate(sorted(fields))
        }
        plot_df_sorted = plot_df.sort_values("EUR (MMSTB)", ascending=True)
        axes[1].barh(
            plot_df_sorted["Well"],
            plot_df_sorted["EUR (MMSTB)"],
            color=plot_df_sorted["Field"].map(field_color_map),
            edgecolor="none", height=0.6,
        )
        axes[1].set_xlabel("EUR (MMSTB)")
        axes[1].set_title(f"By Well ({len(plot_df_sorted)} selected)")
        axes[1].tick_params(axis="y", labelsize=7)

        plt.tight_layout()
        st.pyplot(fig_eur, use_container_width=True)
        plt.close(fig_eur)

        # Chart 2 — Rate forecast (selected wells, rendered ONCE outside any loop)
        st.markdown("#### Rate Forecast to Economic Limit")
        fig_fcast, ax_f = plt.subplots(figsize=(9, 4.5))

        for _, row in plot_df.iterrows():
            qi_w  = row["qi (STB/D)"]
            di_w  = row["Di (%/yr)"] / 100
            b_w   = row["b-factor"]

            if b_w < 0.01:
                t_econ_w = np.log(max(qi_w / max(econ_limit, 1), 1e-9)) / max(di_w, 1e-6)
            else:
                t_econ_w = (((qi_w / max(econ_limit, 1)) ** b_w) - 1) / (b_w * max(di_w, 1e-6))

            t_end_w = int(min(max(t_econ_w, 12), forecast_horizon_years * 12))
            t_w     = np.arange(0, t_end_w + 1, dtype=float)
            q_w     = (qi_w * np.exp(-di_w * t_w) if b_w < 0.01
                       else qi_w / (1 + b_w * di_w * t_w) ** (1 / b_w))

            ax_f.plot(t_w, np.maximum(q_w, 0), label=row["Well"], linewidth=1.2)
            ax_f.axvline(t_end_w, color="grey", linestyle=":", linewidth=0.6, alpha=0.4)

        # axhline, labels, and legend called ONCE — outside the loop
        ax_f.axhline(econ_limit, color="red", linestyle=":", linewidth=1.3,
                     label=f"Econ. limit ({econ_limit:.0f} STB/D)")
        ax_f.set_xlabel("Months from now")
        ax_f.set_ylabel("Oil Rate (STB/D)")
        ax_f.set_title(f"Arps DCA Forecast — {len(plot_df)} wells  (max {forecast_horizon_years} yr)")
        ax_f.legend(fontsize=7, ncol=2)
        ax_f.set_ylim(bottom=0)
        st.pyplot(fig_fcast, use_container_width=True)
        plt.close(fig_fcast)

        # Chart 3 — Decline risk scatter (user-controlled axes)
        st.markdown(f"#### Decline Risk: {scatter_x} vs {scatter_y}")
        fig_b, ax_b = plt.subplots(figsize=(8, 4))

        bubble_sizes   = (plot_df["EUR (MMSTB)"] / max(plot_df["EUR (MMSTB)"].max(), 1e-9) * 300).clip(lower=20)
        scatter_colors = ["#F44336" if v > 1.0 else "#4CAF50" for v in plot_df["b-factor"]]

        ax_b.scatter(plot_df[scatter_x], plot_df[scatter_y],
                     s=bubble_sizes, c=scatter_colors, alpha=0.8, edgecolors="white")
        for _, row in plot_df.iterrows():
            ax_b.annotate(row["Well"], (row[scatter_x], row[scatter_y]),
                          fontsize=7, textcoords="offset points", xytext=(5, 3))
        if scatter_y == "b-factor":
            ax_b.axhline(1.0, color="#FF5722", linestyle="--", linewidth=1,
                         label="b = 1.0 (harmonic threshold)")
            ax_b.legend(fontsize=8)

        ax_b.set_xlabel(scatter_x)
        ax_b.set_ylabel(scatter_y)
        ax_b.set_title("Bubble size ∝ EUR  |  Red = b > 1.0")
        st.pyplot(fig_b, use_container_width=True)
        plt.close(fig_b)

    with st.expander("📖 DCA theory & references"):
        st.markdown("""
        #### Arps Decline Curve Analysis
        Generalised hyperbolic equation (Arps, 1945):
        $$q(t) = \\frac{q_i}{(1 + b \\cdot D_i \\cdot t)^{1/b}}$$

        | Parameter | Meaning | Typical range (conventional) |
        |-----------|---------|-------------------------------|
        | $q_i$ | Initial rate at $t=0$ | Field-dependent |
        | $D_i$ | Nominal decline rate | 0.05–0.50 /yr |
        | $b$ | Arps b-factor | 0 → exponential, 1 → harmonic |

        **b-factor guidance:**
        - $b = 0$: Exponential — constant fractional decline; most conservative,
          preferred by SPE-PRMS for proved reserves booking.
        - $0 < b < 1$: Hyperbolic — most common in conventional reservoirs.
        - $b = 1$: Harmonic — strong pressure support or gravity drainage.
        - $b > 1$: Transient flow (tight/shale) or data quality issue;
          apply a terminal exponential switch before booking reserves.

        ---
        **References**
        - Arps, J.J. (1945). *Analysis of Decline Curves.* Trans. AIME, 160, 228–247.
        - [SPE-PRMS (2018)](https://www.spe.org/en/industry/petroleum-resources-management-system-2018/) §3.4
        - Lee & Wattenbarger (1996). *Gas Reservoir Engineering.* SPE Textbook Vol. 5, Ch. 8.
        - [SPE-168966](https://onepetro.org/SPEATCE/proceedings/13ATCE/All-13ATCE/SPE-168966-MS/176816)
          — Ilk et al., b > 1 in unconventional reservoirs.
        """)

    # ── 9. AI ASSET ADVISOR ──────────────────────────────────────────────────
    st.subheader("🤖 AI Asset Advisor")

    if agent_flags:
        st.markdown("**🛡️ Anomalies detected — review before sanctioning reserves:**")
        
        # 1. Combine flags into a single string with HTML line breaks or list items
        flags_html = "".join([f"<div style='margin-bottom:8px; border-bottom:1px solid #f0f2f6; padding-bottom:4px;'>{flag}</div>" for flag in agent_flags])

        # 2. Wrap in a scrollable div
        st.markdown(f"""
            <div style="
                height: 200px; 
                overflow-y: scroll; 
                border: 1px solid #e6e9ef; 
                border-radius: 8px; 
                padding: 15px; 
                background-color: #ffffff;
                font-family: sans-serif;
                font-size: 0.9rem;
                color: #112233;
            ">
                {flags_html}
            </div>
        """, unsafe_allow_html=True)

    # ── AI DIAGNOSIS TRIGGER ────────────────────────────────────────────────
    if st.button("Run AI Diagnosis", type="primary", key="asset_intel_run_diag"):
        # Prepare the heavy technical context for the AI
        summary_text = results_df.to_string(index=False)
        field_text   = field_summary.to_string(index=False)
        flags_text   = "\n".join(agent_flags) if agent_flags else "No anomalies detected."

        agent_prompt = (
            f"Analyze the DCA results for {len(wells)} wells.\n"
            f"FIELD SUMMARY:\n{field_text}\n"
            f"WELL DATA:\n{summary_text}\n"
            f"ANOMALIES:\n{flags_text}\n\n"
            f"Provide: 1. Field-level reserves summary, 2. Top 3 intervention candidates, "
            f"3. Physical interpretation of anomalies, 4. Next steps."
        )

        with st.spinner(f"Agent reasoning over asset data via {llm_choice}..."):
            # 1. Get the initial report
            report = st.session_state.agent.analyze_reservoir_data(
                results_df, agent_prompt, llm_choice
            )
            
            # 2. Store the result for the global audit trail
            st.session_state.last_asset_diag = report

            # 3. INITIALIZE THE CHAT SESSION
            # We seed the 'asset_analysis_messages' with the first AI response
            st.session_state["asset_analysis_messages"] = [
                {"role": "Consultant", "content": report['deck'] if isinstance(report, dict) else report}
            ]

            # 4. Log to global Audit Trail
            st.session_state.audit_trail.append({
                "Timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Action":       "Asset DCA Diagnosis",
                "Safety_Score": report.get("safety_score", 100) if isinstance(report, dict) else 100,
                "Provider":     llm_choice,
            })

    # ── RENDER RESULTS & CHAT ───────────────────────────────────────────────
    if st.session_state.get("asset_analysis_messages"):
        st.divider()
        st.markdown("### 📋 AI Operational Analysis")
        
        # Prepare the persistent data context for follow-up questions
        # We pass the results dataframe as the "Ground Truth" for the chat
        asset_context = results_df.describe().to_string() + "\n\nFull Results:\n" + results_df.to_string()
        
        # Call the reusable chat component (Strategy 3 logic inside)
        render_industrial_chat(
            context_name="asset_analysis", 
            context_data=asset_context, 
            llm_choice=llm_choice
        )
        
        # Human-in-the-Loop Checkpoint (Always visible below the chat)
        st.info("💡 **HITL Required:** Review AI recommendations before acting on them.")
        st.checkbox("I have reviewed the AI diagnosis.", key="asset_intel_hitl")
        

    if st.session_state.get("last_diagnostic"):
        res = st.session_state.last_diagnostic
        res_text = res["deck"] if isinstance(res, dict) else res

        st.markdown("### 📋 AI Operational Diagnostic & Fix")
        
        with st.expander("📝 View AI Report", expanded=True):
            # 1. WRAP IN A FIXED-HEIGHT CONTAINER
            # Adjust height (e.g., 400 or 500) to fit your design
            with st.container(height=500, border=True):
                # 2. RENDER FORMATTED MARKDOWN
                # We call your cleaning function then render inside the scroll box
                cleaned_content = format_ai_table(res_text)
                st.markdown(cleaned_content, unsafe_allow_html=True)
            
            st.divider()
            st.info("💡 **HITL Required:** Review AI recommendations before acting on them.")
            st.checkbox("I have reviewed the AI diagnosis.", key="asset_intel_hitl")

    # ── 10. EXPORT ───────────────────────────────────────────────────────────
    # Always available once results exist — not gated behind AI diagnosis.
    st.subheader("Export")
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        st.download_button(
            label="📥 Well EUR Report",
            data=results_df.to_csv(index=False),
            file_name=f"well_eur_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="asset_intel_export_well",
        )
    with exp_col2:
        st.download_button(
            label="📥 Field Rollup Report",
            data=field_summary.to_csv(index=False),
            file_name=f"field_rollup_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="asset_intel_export_field",
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — RELPERM GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
 
elif selected_workspace == "RelPerm Generator":
    st.header("🧪 Relative Permeability Generator")
    st.info(
        "Generate ECLIPSE SWOF tables using Corey correlations. "
        "Select a Niger Delta analogue or derive parameters from your k and φ data "
        "when no SCAL measurements are available."
    )

    # ── ANALOGUE DATABASE ────────────────────────────────────────────────────
    # Corey parameters derived from Niger Delta SCAL analogues.
    # Sources: Doust & Omatsola (1990) AAPG Memoir 48;
    #          Schlumberger SPWLA Niger Delta Workshop (2009);
    #          Okpobiri & Etu-Efeotor (1987) NAPE.
    ANALOGUES = {
        "Custom": {
            "swc": 0.20, "sorw": 0.20, "nw": 2.0, "no": 3.0,
            "krw_max": 0.40, "kro_max": 0.90,
            "description": "User-defined — set all parameters manually.",
            "ref": "—",
        },
        "Niger Delta — Shallow Marine Sand": {
            "swc": 0.22, "sorw": 0.18, "nw": 2.8, "no": 3.5,
            "krw_max": 0.45, "kro_max": 0.92,
            "description": "High-energy shoreface/barrier bar sands. High k, well-sorted.",
            "ref": "Doust & Omatsola (1990), AAPG Memoir 48",
        },
        "Niger Delta — Fluvial/Deltaic Sand": {
            "swc": 0.25, "sorw": 0.22, "nw": 3.2, "no": 4.0,
            "krw_max": 0.38, "kro_max": 0.88,
            "description": "Distributary channel fills. Moderate heterogeneity, laminated.",
            "ref": "Schlumberger SPWLA Niger Delta Workshop (2009)",
        },
        "Niger Delta — Deepwater Turbidite": {
            "swc": 0.18, "sorw": 0.15, "nw": 2.2, "no": 3.0,
            "krw_max": 0.55, "kro_max": 0.95,
            "description": "Amalgamated turbidite lobes. Low clay, excellent connectivity.",
            "ref": "Okpobiri & Etu-Efeotor (1987), NAPE",
        },
        "Niger Delta — Tight/Cemented Sand": {
            "swc": 0.32, "sorw": 0.28, "nw": 4.5, "no": 5.5,
            "krw_max": 0.22, "kro_max": 0.75,
            "description": "Diagenetically cemented, deep burial. High Swc, reduced mobility.",
            "ref": "Doust & Omatsola (1990), AAPG Memoir 48",
        },
    }

    # ── ROCK CLASS CLASSIFIER (k, φ → Corey params) ──────────────────────────
    def _classify_rock(k_md: float, phi_frac: float) -> dict:
        """
        Estimate Corey exponents from permeability and porosity using the
        Winland R35 pore-throat radius method (Kolodzie 1980; Pittman 1992).

        log(R35) = 0.732 + 0.588·log(k) − 0.864·log(φ·100)

        Rock classes and their typical Corey parameters are calibrated to
        Niger Delta SCAL analogue data.

        References:
          Kolodzie (1980) SPE-9382.
          Pittman (1992) AAPG Bulletin 76(2).
        """
        if k_md <= 0 or phi_frac <= 0:
            return None
        log_r35 = (0.732
                   + 0.588 * np.log10(k_md)
                   - 0.864 * np.log10(phi_frac * 100))
        r35 = 10 ** log_r35

        if r35 > 10:
            label = "Class 1 — Mega-porous  (R35 > 10 μm)"
            nw, no, krw_max, kro_max = 2.0, 2.8, 0.55, 0.95
        elif r35 > 2:
            label = "Class 2 — Macro-porous  (R35 2–10 μm)"
            nw, no, krw_max, kro_max = 2.8, 3.5, 0.42, 0.90
        elif r35 > 0.5:
            label = "Class 3 — Meso-porous  (R35 0.5–2 μm)"
            nw, no, krw_max, kro_max = 3.8, 4.5, 0.28, 0.80
        else:
            label = "Class 4 — Micro-porous  (R35 < 0.5 μm)"
            nw, no, krw_max, kro_max = 5.0, 6.0, 0.15, 0.65

        # Swc estimate from empirical k-Swc regression (Niger Delta analogues)
        swc_est = float(np.clip(0.50 - 0.025 * np.log10(max(k_md, 1)), 0.10, 0.45))

        return {
            "rock_class": label,
            "r35_um":     round(r35, 2),
            "nw":         round(nw, 2),
            "no":         round(no, 2),
            "krw_max":    round(krw_max, 3),
            "kro_max":    round(kro_max, 3),
            "swc_est":    round(swc_est, 3),
        }

    def _corey_table(swc, sorw, nw, no, krw_max, kro_max, n_points=25):
        sw      = np.linspace(swc, 1 - sorw, n_points)
        sw_norm = np.clip((sw - swc) / (1 - sorw - swc), 0, 1)
        return pd.DataFrame({
            "Sw":  sw,
            "Krw": krw_max * sw_norm ** nw,
            "Kro": kro_max * (1 - sw_norm) ** no,
            "Pc":  np.zeros(n_points),
        })

    def _to_eclipse_swof(df, analogue, swc, sorw, nw, no, krw_max, kro_max):
        header = (
            f"-- SWOF table — Reservoir Agent\n"
            f"-- Analogue : {analogue}\n"
            f"-- Swc={swc:.3f}  Sorw={sorw:.3f}  nw={nw:.2f}  no={no:.2f}\n"
            f"-- Krw_max={krw_max:.3f}  Kro_max={kro_max:.3f}\n"
            f"-- {'Sw':<12} {'Krw':<12} {'Kro':<12} {'Pc':<10}\n"
            f"SWOF\n"
        )
        rows = "".join(
            f"  {r.Sw:.6f}    {r.Krw:.6f}    {r.Kro:.6f}    {r.Pc:.4f}\n"
            for r in df.itertuples()
        )
        return header + rows + "/\n"
    
    def _corey_table_sgof(sgc, sorg, ng, nog, krg_max, kro_max_g, n_points=25):
        """
        Generate SGOF table: gas-oil relative permeability.
        Sg axis runs from Sgc (connate gas) to 1 - Swc - Sorg.
        """
        #sg_max = 1 - swc - sorg  # maximum gas saturation
        sg_max = float(1 - float(swc) - float(sorg))
        sg     = np.linspace(sgc, sg_max, n_points)
        sg_norm = np.clip((sg - sgc) / (sg_max - sgc), 0, 1)
        
        return pd.DataFrame({
            "Sg":  sg,
            "Krg": krg_max  * sg_norm ** ng,
            "Krog": kro_max_g * (1 - sg_norm) ** nog,
            "Pc":  np.zeros(n_points),
        })

    def _to_eclipse_sgof(df, analogue, sgc, sorg, ng, nog, krg_max, kro_max_g):
        header = (
            f"-- SGOF table — Reservoir Agent\n"
            f"-- Analogue : {analogue}\n"
            f"-- Sgc={sgc:.3f}  Sorg={sorg:.3f}  ng={ng:.2f}  nog={nog:.2f}\n"
            f"-- Krg_max={krg_max:.3f}  Kro_max(g)={kro_max_g:.3f}\n"
            f"-- {'Sg':<12} {'Krg':<12} {'Krog':<12} {'Pc':<10}\n"
            f"SGOF\n"
        )
        rows = "".join(
            f"  {r.Sg:.6f}    {r.Krg:.6f}    {r.Krog:.6f}    {r.Pc:.4f}\n"
            for r in df.itertuples()
        )
        return header + rows + "/\n"
        
    # ── RESET CALLBACK ───────────────────────────────────────────────────────
    def _reset_relperm():
        for key in ["relperm_result", "relperm_swof_str"]:
            st.session_state.pop(key, None)

    # ── 1. INPUT MODE ────────────────────────────────────────────────────────
    st.subheader("Input Mode")
    input_mode = st.radio(
        "Parameter source:",
        ["Analogue / Manual", "Derive from k and φ (Winland R35)"],
        horizontal=True,
        key="relperm_input_mode",
        on_change=_reset_relperm,
        help=(
            "Use 'Analogue / Manual' when you have SCAL data or a known field analogue. "
            "Use 'Derive from k and φ' when no SCAL data exists — the tool classifies "
            "your rock using the Winland R35 method and suggests Corey exponents from "
            "Niger Delta calibrated correlations (Kolodzie 1980, SPE-9382)."
        ),
    )

    # ── 2. PARAMETERS ────────────────────────────────────────────────────────
    st.subheader("Parameters")

    if input_mode == "Analogue / Manual":

        preset = st.selectbox(
            "Regional Analogue:",
            list(ANALOGUES.keys()),
            key="relperm_preset",
            on_change=_reset_relperm,
        )
        a = ANALOGUES[preset]
        st.caption(f"_{a['description']}_  \n**Ref:** {a['ref']}")

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            swc     = st.number_input("Connate Water Saturation (Swc)",
                                      0.0, 0.5, a["swc"], 0.01,
                                      key="relperm_swc",
                                      help="Irreducible water saturation. "
                                           "Below this Sw, water is immobile.")
            sorw    = st.number_input("Residual Oil Saturation (Sorw)",
                                      0.0, 0.5, a["sorw"], 0.01,
                                      key="relperm_sorw",
                                      help="Oil saturation below which oil is immobile "
                                           "during waterflooding.")
            krw_max = st.slider("Max Krw (at 1−Sorw)", 0.05, 1.0, a["krw_max"], 0.01,
                                key="relperm_krw_max",
                                help="End-point water relative permeability. "
                                     "Typically 0.3–0.6 for water-wet systems.")
        with col_in2:
            nw      = st.slider("Water Corey Exponent (nw)", 1.0, 8.0, a["nw"], 0.1,
                                key="relperm_nw",
                                help="Controls curvature of Krw. Higher nw = more "
                                     "piston-like displacement. Typical: 2–4.")
            no      = st.slider("Oil Corey Exponent (no)",   1.0, 8.0, a["no"], 0.1,
                                key="relperm_no",
                                help="Controls curvature of Kro. Typical: 2–6.")
            kro_max = st.slider("Max Kro (at Swc)", 0.1, 1.0, a["kro_max"], 0.01,
                                key="relperm_kro_max",
                                help="End-point oil relative permeability at connate "
                                     "water saturation. Often ≈ 1.0 for clean sands.")
        rock_class_info = None

    else:  # Derive from k and φ
        col_kphi1, col_kphi2 = st.columns(2)
        with col_kphi1:
            k_input   = st.number_input(
                "Permeability k (mD)", min_value=0.01, max_value=20000.0,
                value=300.0, step=10.0, key="relperm_k",
                help="Absolute permeability from core or log-derived k. "
                     "Used to compute Winland R35 pore-throat radius.",
            )
        with col_kphi2:
            phi_input = st.number_input(
                "Porosity φ (fraction)", min_value=0.01, max_value=0.45,
                value=0.25, step=0.01, key="relperm_phi",
                help="Effective porosity (fraction, not percent). "
                     "Combined with k to classify rock type via Winland R35.",
            )

        rock_class_info = _classify_rock(k_input, phi_input)

        if rock_class_info:
            st.info(
                f"**Rock classification:** {rock_class_info['rock_class']}  \n"
                f"Winland R35 = **{rock_class_info['r35_um']} μm**  \n"
                f"Suggested Swc = {rock_class_info['swc_est']}  |  "
                f"nw = {rock_class_info['nw']}  |  no = {rock_class_info['no']}  |  "
                f"Krw_max = {rock_class_info['krw_max']}  |  Kro_max = {rock_class_info['kro_max']}"
            )

        # Still expose sliders so engineer can override the suggested values
        st.markdown("**Override suggested parameters if needed:**")
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            swc     = st.number_input("Swc", 0.0, 0.5, rock_class_info["swc_est"], 0.01,
                                      key="relperm_swc")
            sorw    = st.number_input("Sorw", 0.0, 0.5, 0.20, 0.01, key="relperm_sorw")
            krw_max = st.slider("Max Krw", 0.05, 1.0, rock_class_info["krw_max"], 0.01,
                                key="relperm_krw_max")
        with col_in2:
            nw      = st.slider("nw", 1.0, 8.0, rock_class_info["nw"], 0.1,
                                key="relperm_nw")
            no      = st.slider("no", 1.0, 8.0, rock_class_info["no"], 0.1,
                                key="relperm_no")
            kro_max = st.slider("Max Kro", 0.1, 1.0, rock_class_info["kro_max"], 0.01,
                                key="relperm_kro_max")

        preset = f"Winland R35 — k={k_input} mD, φ={phi_input}"

    # ── 3. GENERATE ──────────────────────────────────────────────────────────
    if st.button("Generate SWOF Table", type="primary", key="relperm_generate"):
        if 1 - sorw - swc <= 0:
            st.error("Invalid saturations: (1 − Sorw − Swc) must be > 0.")
        else:
            df_swof  = _corey_table(swc, sorw, nw, no, krw_max, kro_max)
            swof_str = _to_eclipse_swof(df_swof, preset, swc, sorw, nw, no, krw_max, kro_max)
            st.session_state["relperm_result"]   = df_swof
            st.session_state["relperm_swof_str"] = swof_str
            
    # ── SGOF — GAS-OIL RELATIVE PERMEABILITY ─────────────────────────────────
    st.divider()
    st.subheader("SGOF Table (Gas-Oil)")
    st.info(
        "Required for any reservoir with a gas cap, solution gas drive, or gas"
        "injection. SWOF alone is insufficient for a three-phase ECLIPSE model —"
        "both SWOF and SGOF must be present in the PROPS section.",
        icon="ℹ️",
    )

    with st.expander("📖 SGOF — when you need it and how it relates to SWOF"):
        st.markdown("""
        #### SGOF vs SWOF

        ECLIPSE black oil models with three mobile phases (oil, water, gas) require
        **both** keywords in the PROPS section:

        | Keyword | Phase pair | Saturation axis | Typical displacement |
        |---------|-----------|-----------------|----------------------|
        | `SWOF`  | Water–Oil | Sw (water sat.) | Waterflood |
        | `SGOF`  | Gas–Oil   | Sg (gas sat.)   | Gas cap expansion / gas injection |

        At any grid cell, ECLIPSE combines Kro from SWOF and Kro from SGOF using
        **Stone's Model I or II** (set with `STONE1` or `STONE2` in RUNSPEC) to
        compute the three-phase oil relative permeability.

        #### SGOF Parameters

        | Parameter | Meaning |
        |-----------|---------|
        | $S_{gc}$ | Critical gas saturation — minimum Sg for gas to flow |
        | $S_{org}$ | Residual oil to gas displacement |
        | $n_g$ | Gas Corey exponent — controls Krg curvature |
        | $n_{og}$ | Oil Corey exponent in SGOF (can differ from SWOF $n_o$) |
        | $K_{rg}^{max}$ | End-point Krg at maximum gas saturation |
        | $K_{ro}^{max}(g)$ | End-point Kro at $S_g = S_{gc}$ (should match SWOF $K_{ro}^{max}$) |

        **Niger Delta context:** most Niger Delta full-field models have an active
        gas cap or gas injection scheme. Omitting SGOF will cause the simulator to
        abort with a missing table error as soon as gas saturation becomes non-zero.

        **References**
        - Stone, H.L. (1970). *Probability model for estimating three-phase relative
          permeability.* JPT 22(2), 214–218. SPE-2116.
        - Stone, H.L. (1973). *Estimation of three-phase relative permeability and
          residual oil data.* JCPT 12(4). SPE-4436.
        - Corey, A.T. (1954). *The interrelation between gas and oil relative
          permeabilities.* Producers Monthly 19(1), 38–41.
        """)

    # SGOF parameters — sensible Niger Delta defaults
    # Gas exponents are typically lower than water exponents (gas is more mobile)
    st.markdown("**SGOF Parameters**")
    sgof_col1, sgof_col2 = st.columns(2)

    with sgof_col1:
        sgc = st.number_input(
            "Critical Gas Saturation (Sgc)",
            min_value=0.0, max_value=0.3, value=0.05, step=0.01,
            key="relperm_sgc",
            help=(
                "Minimum gas saturation at which gas begins to flow. "
                "Typically 0.02–0.10 for Niger Delta sands. "
                "Below Sgc, gas is trapped and immobile — this is the "
                "'critical' or 'connate' gas saturation."
            ),
        )
        sorg = st.number_input(
            "Residual Oil to Gas (Sorg)",
            min_value=0.0, max_value=0.5, value=0.15, step=0.01,
            key="relperm_sorg",
            help=(
                "Residual oil saturation remaining after gas displacement. "
                "Generally lower than Sorw because gas is a more efficient "
                "displacing agent in gravity-stable situations. "
                "Typical range: 0.10–0.25."
            ),
        )
        krg_max = st.slider(
            "Max Krg (at Sg_max)",
            min_value=0.05, max_value=1.0, value=0.80, step=0.01,
            key="relperm_krg_max",
            help=(
                "End-point gas relative permeability at maximum gas saturation "
                "(Sg = 1 − Swc − Sorg). Typically 0.6–0.9 for clean sands. "
                "Higher than Krw_max because gas viscosity is much lower than water."
            ),
        )

    with sgof_col2:
        ng = st.slider(
            "Gas Corey Exponent (ng)",
            min_value=1.0, max_value=8.0, value=1.5, step=0.1,
            key="relperm_ng",
            help=(
                "Controls curvature of the Krg curve. "
                "Gas exponents are typically lower (1.0–2.5) than water exponents "
                "because gas flows more readily through the pore network. "
                "Higher ng = more piston-like gas displacement."
            ),
        )
        nog = st.slider(
            "Oil Exponent in SGOF (nog)",
            min_value=1.0, max_value=8.0, value=no, step=0.1,
            key="relperm_nog",
            help=(
                "Oil Corey exponent for the gas-oil system. "
                "Often set equal to the SWOF oil exponent (no) as a first pass, "
                "but can differ — gas displacement can leave a different residual "
                "oil distribution than waterflooding."
            ),
        )
        kro_max_g = st.slider(
            "Max Kro in SGOF (at Sgc)",
            min_value=0.1, max_value=1.0, value=kro_max, step=0.01,
            key="relperm_kro_max_g",
            help=(
                "End-point oil relative permeability in the gas-oil system, "
                "evaluated at critical gas saturation. Should be consistent with "
                "Kro_max from SWOF — if they differ significantly, Stone's model "
                "will produce discontinuities in three-phase Kro that can cause "
                "convergence problems in the simulator."
            ),
        )
    
    
    if st.button("Generate SGOF Table", type="primary", key="relperm_generate_sgof"):
        #sg_max = 1 - swc - sorg
        sg_max = float(1 - float(swc) - float(sorg))
        if sg_max <= sgc:
            st.error(
                f"Invalid saturations: Sg_max (1 − Swc − Sorg = {sg_max:.3f}) "
                f"must be greater than Sgc ({sgc:.3f})."
            )
        else:
            df_sgof  = _corey_table_sgof(sgc, sorg, ng, nog, krg_max, kro_max_g)
            sgof_str = _to_eclipse_sgof(
                df_sgof, preset, sgc, sorg, ng, nog, krg_max, kro_max_g
            )
            st.session_state["relperm_sgof_result"] = df_sgof
            st.session_state["relperm_sgof_str"]    = sgof_str

    
    # ── 4. OUTPUTS (persisted in session_state) ───────────────────────────────
    
    if "relperm_result" in st.session_state:
        df_swof  = st.session_state["relperm_result"]
        swof_str = st.session_state["relperm_swof_str"]
        
    if "relperm_sgof_result" in st.session_state:
        df_sgof  = st.session_state["relperm_sgof_result"]
        sgof_str = st.session_state["relperm_sgof_str"]

        with st.expander("View Results"):
            st.subheader("Results")
            chart_col, code_col = st.columns([2, 1])
            with chart_col:
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.plot(df_swof["Sw"], df_swof["Krw"], "b-o",  markersize=3,
                        linewidth=1.8, label="Krw (water)")
                ax.plot(df_swof["Sw"], df_swof["Kro"], "r-s",  markersize=3,
                        linewidth=1.8, label="Kro (oil)")

                # Cross-over point
                cross_idx = (df_swof["Krw"] - df_swof["Kro"]).abs().idxmin()
                cross_sw  = df_swof.loc[cross_idx, "Sw"]
                cross_kr  = df_swof.loc[cross_idx, "Krw"]
                ax.axvline(cross_sw, color="grey", linestyle="--", linewidth=1,
                           label=f"Cross-over Sw = {cross_sw:.3f}")
                ax.annotate(f"Sw={cross_sw:.3f}", (cross_sw, cross_kr),
                            textcoords="offset points", xytext=(6, 4), fontsize=8)

                ax.set_xlabel("Water Saturation (Sw)")
                ax.set_ylabel("Relative Permeability (Kr)")
                ax.set_title(f"Corey RelPerm — {preset}")
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

                # Cross-over interpretation
                st.caption(
                    f"**Cross-over Sw = {cross_sw:.3f}** — "
                    f"above this saturation water mobility exceeds oil mobility. "
                    f"In a waterflood, this is approximately the front saturation "
                    f"at breakthrough under piston-like displacement."
                )

            with code_col:
                st.markdown("**ECLIPSE SWOF Syntax**")
                st.code(swof_str, language="plaintext")
                
                sgof_chart_col, sgof_code_col = st.columns([2, 1])
                with sgof_chart_col:
                    fig_g, ax_g = plt.subplots(figsize=(7, 4))
                    ax_g.plot(df_sgof["Sg"], df_sgof["Krg"],  "g-o", markersize=3,
                              linewidth=1.8, label="Krg (gas)")
                    ax_g.plot(df_sgof["Sg"], df_sgof["Krog"], "r-s", markersize=3,
                              linewidth=1.8, label="Krog (oil)")

                    # Cross-over
                    cross_idx_g = (df_sgof["Krg"] - df_sgof["Krog"]).abs().idxmin()
                    cross_sg    = df_sgof.loc[cross_idx_g, "Sg"]
                    cross_krg   = df_sgof.loc[cross_idx_g, "Krg"]
                    ax_g.axvline(cross_sg, color="grey", linestyle="--", linewidth=1,
                                 label=f"Cross-over Sg = {cross_sg:.3f}")
                    ax_g.annotate(f"Sg={cross_sg:.3f}", (cross_sg, cross_krg),
                                  textcoords="offset points", xytext=(6, 4), fontsize=8)

                    ax_g.set_xlabel("Gas Saturation (Sg)")
                    ax_g.set_ylabel("Relative Permeability (Kr)")
                    ax_g.set_title(f"Gas-Oil RelPerm (SGOF) — {preset}")
                    ax_g.set_xlim(0, 1)
                    ax_g.set_ylim(0, 1)
                    ax_g.legend(fontsize=9)
                    ax_g.grid(True, alpha=0.3)
                    st.pyplot(fig_g, use_container_width=True)
                    plt.close(fig_g)

                    st.caption(
                        f"**Cross-over Sg = {cross_sg:.3f}** — above this saturation gas "
                        f"mobility exceeds oil mobility. In a gas-cap drive reservoir this "
                        f"approximates the Sg at which gas tonguing becomes significant."
                    )

                    with sgof_code_col:
                        st.markdown("**ECLIPSE SGOF Syntax**")
                        st.code(sgof_str, language="plaintext")            

        # Reference table
        with st.expander("View SWOF saturation table"):
            st.dataframe(
                df_swof.style.format({
                    "Sw": "{:.4f}", "Krw": "{:.6f}",
                    "Kro": "{:.6f}", "Pc": "{:.4f}",
                }),
                use_container_width=True,
            )
        

        with st.expander("View SGOF saturation table"):
            st.dataframe(
                df_sgof.style.format({
                    "Sg": "{:.4f}", "Krg": "{:.6f}",
                    "Krog": "{:.6f}", "Pc": "{:.4f}",
                }),
                use_container_width=True,
            )
        
  
        if rock_class_info:
            with st.expander("📖 Rock classification — Winland R35 method"):
                st.markdown(f"""
                **Classified as:** {rock_class_info['rock_class']}

                **Winland R35 pore-throat radius:** {rock_class_info['r35_um']} μm

                The R35 method estimates the pore-throat radius at 35% mercury
                saturation from routine core data:

                $$\\log(R_{{35}}) = 0.732 + 0.588 \\cdot \\log(k) - 0.864 \\cdot \\log(\\phi \\cdot 100)$$

                Corey exponents are then assigned from Niger Delta SCAL analogue
                calibration data for each rock class.

                | Rock Class | R35 (μm) | nw | no | Krw_max |
                |------------|----------|----|----|---------|
                | Class 1 — Mega-porous | > 10 | 2.0 | 2.8 | 0.55 |
                | Class 2 — Macro-porous | 2–10 | 2.8 | 3.5 | 0.42 |
                | Class 3 — Meso-porous | 0.5–2 | 3.8 | 4.5 | 0.28 |
                | Class 4 — Micro-porous | < 0.5 | 5.0 | 6.0 | 0.15 |

                **References**
                - Kolodzie (1980). *Production results and porosity and permeability of
                  Spindle Field, Colorado.* SPE-9382.
                - Pittman (1992). *Relationship of porosity and permeability to various
                  parameters derived from mercury injection–capillary pressure curves.*
                  AAPG Bulletin 76(2), 191–198.
                - Corey (1954). *The interrelation between gas and oil relative
                  permeabilities.* Producers Monthly, 19(1), 38–41.
                """)

        with st.expander("📖 Corey correlation — theory & references"):
            st.markdown("""
            #### Corey Relative Permeability Correlation

            $$K_{rw}(S_w) = K_{rw}^{max} \\cdot \\left(\\frac{S_w - S_{wc}}{1 - S_{orw} - S_{wc}}\\right)^{n_w}$$

            $$K_{ro}(S_w) = K_{ro}^{max} \\cdot \\left(1 - \\frac{S_w - S_{wc}}{1 - S_{orw} - S_{wc}}\\right)^{n_o}$$

            | Parameter | Physical meaning |
            |-----------|-----------------|
            | $S_{wc}$ | Connate (irreducible) water saturation |
            | $S_{orw}$ | Residual oil saturation to waterflood |
            | $n_w$ | Water Corey exponent — controls Krw curvature |
            | $n_o$ | Oil Corey exponent — controls Kro curvature |
            | $K_{rw}^{max}$ | End-point Krw at $S_w = 1 - S_{orw}$ |
            | $K_{ro}^{max}$ | End-point Kro at $S_w = S_{wc}$ |

            **When to use this approach (no SCAL):**
            Corey correlations are the industry-standard substitute when laboratory
            SCAL (Special Core Analysis) measurements are unavailable.
            The exponents should be calibrated to field production history or
            analogue SCAL data. The Niger Delta analogues here are derived from
            published petrophysical studies of similar depositional systems.

            ---
            **References**
            - Corey, A.T. (1954). *The interrelation between gas and oil relative
              permeabilities.* Producers Monthly, 19(1), 38–41.
            - Brooks, R.H. & Corey, A.T. (1964). *Hydraulic properties of porous media.*
              Colorado State University Hydrology Paper No. 3.
            - Doust, H. & Omatsola, E. (1990). *Niger Delta.* AAPG Memoir 48, 201–238.
            - Schlumberger (2009). *Petrophysics in the Niger Delta.*
              SPWLA Annual Symposium Workshop Notes.
            """)
        
        # ── EXPORT ───────────────────────────────────────────────────────────  
        # Combined PROPS export — both tables in one .INC file
        st.subheader("Export")
        exp_c1, exp_c2, exp_g1, exp_g2, exp_g3 = st.columns(5)
        
        #exp_c1, exp_c2 = st.columns(2)
        with exp_c1:
            st.download_button(
                label="📥 SWOF INC",
                data=swof_str,
                file_name=f"relperm_{datetime.now().strftime('%Y%m%d_%H%M')}.inc",
                mime="text/plain",
                key="relperm_download_inc",
            )
        with exp_c2:
            st.download_button(
                label="📥 SWOF CSV",
                data=df_swof.to_csv(index=False),
                file_name=f"relperm_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="relperm_download_csv",
            )

        with exp_g1:
            st.download_button(
                label="📥 SGOF INC",
                data=sgof_str,
                file_name=f"sgof_{datetime.now().strftime('%Y%m%d_%H%M')}.inc",
                mime="text/plain",
                key="relperm_download_sgof",
            )
        with exp_g2:
            st.download_button(
                label="📥 SGOF CSV",
                data=df_sgof.to_csv(index=False),
                file_name=f"sgof_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="relperm_download_sgof_csv",
            )
        with exp_g3:
            # Combined SWOF + SGOF in a single PROPS .INC — most useful for deck assembly
            if "relperm_swof_str" in st.session_state:
                combined = (
                    "-- Combined PROPS RelPerm tables\n"
                    "-- Generated by Reservoir Agent\n\n"
                    + st.session_state["relperm_swof_str"]
                    + "\n"
                    + sgof_str
                )
                st.download_button(
                    label="📥 SWOF + SGOF INC",
                    data=combined,
                    file_name=f"relperm_props_{datetime.now().strftime('%Y%m%d_%H%M')}.inc",
                    mime="text/plain",
                    key="relperm_download_combined",
                    help=(
                        "Single .INC file containing both SWOF and SGOF tables, "
                        "ready to include in your PROPS section with: "
                        "INCLUDE 'relperm_props.inc' /"
                    ),
                )
            else:
                st.caption("Generate SWOF first to enable combined export.")

        
        # ── AI INTERPRETATION ─────────────────────────────────────────────────────
        # ── AI INTERPRETATION SECTION ─────────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🤖 AI Petrophysical Review")

        # 1. Initialize result container if not exists
        if "relperm_ai_review_done" not in st.session_state:
            st.session_state.relperm_ai_review_done = False

        if st.button("Interpret RelPerm", key="relperm_ai_interpret"):
            if "relperm_result" not in st.session_state:
                st.warning("Generate a SWOF table first.")
            else:
                # Calculate Crossover Sw (where Krw and Kro are closest)
                df_swof = st.session_state["relperm_result"]
                idx = (df_swof["Krw"] - df_swof["Kro"]).abs().idxmin()
                cross_sw = df_swof.loc[idx, "Sw"]

                # Build the technical prompt
                interp_prompt = (
                    f"Review these Corey parameters for the {preset} analogue.\n"
                    f"Parameters: Swc={swc:.3f}, Sorw={sorw:.3f}, nw={nw:.2f}, no={no:.2f}, "
                    f"Krw_max={krw_max:.3f}, Kro_max={kro_max:.3f}. "
                    f"Calculated Crossover Sw: {cross_sw:.3f}.\n"
                    f"Analyze for geological consistency, waterflood sweep efficiency, and simulation risks."
                )

                with st.spinner("AI is performing petrophysical audit..."):
                    # Call agent with the DATAFRAME and the PROMPT
                    report = st.session_state.agent.analyze_reservoir_data(
                        df_swof, interp_prompt, llm_choice
                    )
                    
                    # Initialize the specific chat history for this tab
                    # We use the 'relperm_messages' key that render_industrial_chat expects
                    st.session_state["relperm_messages"] = [
                        {"role": "Consultant", "content": report['deck'] if isinstance(report, dict) else report}
                    ]
                    st.session_state.relperm_ai_review_done = True

        # 2. THE REUSABLE CHAT COMPONENT (Strategy 3 inside)
        if st.session_state.relperm_ai_review_done:
            # Pass the SWOF table as the persistent technical context
            context_data = st.session_state["relperm_result"].to_string()
            
            render_industrial_chat(
                context_name="relperm", 
                context_data=context_data, 
                llm_choice=llm_choice
            )
                    

elif selected_workspace == "Governance & Audit":
    st.header("🛡️ Compliance & Audit Trail")

    # ── 1. SESSION METRICS ───────────────────────────────────────────────────
    audit_trail = st.session_state.get("audit_trail", [])
    audit_df    = pd.DataFrame(audit_trail) if audit_trail else pd.DataFrame()

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Total AI Runs", len(audit_df) if not audit_df.empty else 0)
    with m2:
        avg_score = (
            round(audit_df["Safety_Score"].mean(), 1)
            if not audit_df.empty and "Safety_Score" in audit_df.columns
            else "—"
        )
        st.metric(
            "Avg Safety Score",
            avg_score,
            help=(
                "Mean safety score across all AI runs this session. "
                "Score is penalised by 15 points per fact-check anomaly "
                "detected in the AI response. Target: ≥ 70."
            ),
        )
    with m3:
        providers = (
            audit_df["Provider"].nunique()
            if not audit_df.empty and "Provider" in audit_df.columns
            else 0
        )
        st.metric("LLM Providers Used", providers)
    with m4:
        low_score_runs = (
            int((audit_df["Safety_Score"] < 70).sum())
            if not audit_df.empty and "Safety_Score" in audit_df.columns
            else 0
        )
        st.metric(
            "Low-Score Runs (< 70)",
            low_score_runs,
            delta=f"{low_score_runs} require review" if low_score_runs else None,
            delta_color="inverse",
        )

    st.divider()

    # ── 2. AUDIT TRAIL TABLE ─────────────────────────────────────────────────
    st.subheader("Session Audit Trail")

    if audit_df.empty:
        st.info(
            "No AI runs recorded yet this session. "
            "Run a diagnostic, DCA analysis, or RelPerm interpretation "
            "to populate the audit trail."
        )
    else:
        # Filtering controls
        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            action_options = ["All"] + sorted(audit_df["Action"].unique().tolist()) \
                if "Action" in audit_df.columns else ["All"]
            filter_action = st.selectbox(
                "Filter by Action", action_options, key="audit_filter_action"
            )
        with filter_col2:
            provider_options = ["All"] + sorted(audit_df["Provider"].unique().tolist()) \
                if "Provider" in audit_df.columns else ["All"]
            filter_provider = st.selectbox(
                "Filter by Provider", provider_options, key="audit_filter_provider"
            )
        with filter_col3:
            score_threshold = st.slider(
                "Min Safety Score",
                min_value=0, max_value=100, value=0,
                key="audit_score_threshold",
                help="Show only runs at or above this safety score.",
            )

        # Apply filters
        filtered_df = audit_df.copy()
        if filter_action != "All" and "Action" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Action"] == filter_action]
        if filter_provider != "All" and "Provider" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Provider"] == filter_provider]
        if "Safety_Score" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Safety_Score"] >= score_threshold]

        # Colour-coded safety score column
        def _score_colour(val):
            if isinstance(val, (int, float)):
                if val >= 80:
                    return "background-color: #1b5e20; color: white"
                elif val >= 60:
                    return "background-color: #f57f17; color: white"
                else:
                    return "background-color: #b71c1c; color: white"
            return ""

        styled = filtered_df.style.map(
            _score_colour,
            subset=["Safety_Score"] if "Safety_Score" in filtered_df.columns else [],
        )
        # Applies function to each column
        #df.style.apply(lambda col: ['background-color: yellow' if x > 0 else '' for x in col])

        st.dataframe(styled, use_container_width=True)
        st.caption(
            "🟢 Score ≥ 80 — acceptable  |  "
            "🟡 60–79 — review recommended  |  "
            "🔴 < 60 — HITL sign-off required before acting on output"
        )

        # Export
        st.download_button(
            label="📥 Export Audit Trail",
            data=filtered_df.to_csv(index=False),
            file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="audit_export",
        )

    # ── 3. COMPLIANCE FRAMEWORK ──────────────────────────────────────────────
    st.divider()
    st.subheader("Compliance Framework")

    with st.expander("📋 Applicable Standards & Governance", expanded=False):
        st.markdown("""
        This tool operates within the following regulatory and technical frameworks.
        AI outputs are advisory only — all decisions require qualified engineer sign-off.

        | Framework | Scope | Relevance to this tool |
        |-----------|-------|------------------------|
        | **SPE-PRMS (2018)** | Reserves classification & reporting | DCA/EUR methodology (§3.4), uncertainty disclosure |
        | **DPR Nigeria — Reserves Guidelines** | Nigerian upstream reporting | Field-level EUR aggregation and reporting |
        | **OSPAR Decision 98/3** | Offshore decommissioning | Abandonment timing flags in DCA |
        | **ISO 13703** | Petroleum reservoir engineering | Simulation deck QC standards |
        | **GDPR / NDPR** | Data privacy | Zero Data Retention mode for sensitive well data |

        #### AI Governance Principles Applied
        - **Human-in-the-Loop (HITL):** No AI output is actioned without engineer
          review and explicit sign-off.
        - **Zero Data Retention:** Deck content and production data are not stored
          beyond the active session unless explicitly exported by the user.
        - **Groundtruth anchoring:** All keyword suggestions are validated against
          the ECLIPSE / OPM  keyword database before being returned.
        - **Audit trail:** Every AI inference is logged with timestamp, action type,
          safety score, and provider for post-session review.
        - **Safety scoring:** Responses are penalised 15 points per detected anomaly.
          Scores below 70 trigger a mandatory HITL review flag.

        **References**
        - [SPE-PRMS (2018)](https://www.spe.org/en/industry/petroleum-resources-management-system-2018/)
        - [DPR Nigeria Reserves Guidelines](https://www.nuprc.gov.ng)
        - [OSPAR Decision 98/3](https://www.ospar.org/convention/decisions)
        """)

    # ── 4. CLEAR SESSION ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Session Management")

    clear_col1, clear_col2 = st.columns([1, 3])
    with clear_col1:
        if st.button("🗑️ Clear Session", type="secondary", key="audit_clear_session"):
            keys_to_clear = [
                "audit_trail", "last_diagnostic",
                "relperm_result", "relperm_swof_str",
                "relperm_sgof_result", "relperm_sgof_str", "relperm_ai_review",
                "asset_intel_hitl", "asset_intel_selected_wells",
            ]
            for key in keys_to_clear:
                st.session_state.pop(key, None)
            st.success("Session cleared. All AI outputs and audit records removed.")
            st.rerun()
    with clear_col2:
        st.caption(
            "Clears all AI outputs, audit records, and cached results for this session. "
            "Exported files are unaffected. This action cannot be undone."
        )

  
# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — USER GUIDE  (own tab, merged from sidebar + governance)
# ─────────────────────────────────────────────────────────────────────────────
 
elif selected_workspace == "User Guide":
    st.header("📖 User Guide")
    st.info(
        "New to the Exzing Reservoir Agent? Start here. "
        "Each section covers one workspace with step-by-step instructions and tips."
    )
 
    VIDEO_URLS = {
        "chapter-1-debug": "https://youtu.be/0XzDv_0Tmvs",
        "chapter-2-asset": "https://youtu.be/gA9IlXxkEi4",
        "chapter-3-relperm": "https://youtu.be/AlxsY8k4LD0",
    }
    if VIDEO_URLS:
        st.video(VIDEO_URLS["chapter-1-debug"])
        st.video(VIDEO_URLS["chapter-2-asset"])
        st.video(VIDEO_URLS["chapter-3-relperm"])
    else:
        st.info("📹 Video walkthrough coming soon. Use the written guide below.")
 
    st.divider()
 
    tab_start, tab_debug, tab_dca, tab_relperm, tab_gov = st.tabs([
        "🚀 Getting Started",
        "🔧 Simulator Debugger",
        "📈 Asset Intelligence",
        "🧪 RelPerm Generator",
        #"📄 Deck Generator",
        "🛡️ Governance",
    ])
 
    with tab_start:
        st.markdown("""
        #### What is the Exzing Reservoir Agent?
        An AI-powered technical consultant for petroleum reservoir engineers.
        It combines domain-locked language models with verified ECLIPSE /
        OPM  keyword groundtruth to provide accurate, hallucination-resistant
        outputs — with a full audit trail and HITL enforcement.
 
        #### Access
        1. Search **"Exzing Reservoir Management"** in the Azure Portal.
        2. Purchase a **Standard Plan**.
        3. Click **Configure Account** → **Launch Reservoir Agent**.
 
        #### Reasoning Engine (sidebar)
        - **GROQ:** High-speed open-source model — best for rapid iteration.
        - **AZURE:** High-compliance GPT-4o endpoint — best for final outputs and audit.
 
        #### Governance principles
        - Every AI response is scored for technical integrity (target ≥ 70%).
        - All outputs require HITL sign-off before export.
        - No well data or deck content is stored beyond the active session.
        - The full session audit trail is exportable from the Governance tab.
        """)
 
    with tab_debug:
        st.markdown("""
        #### Purpose
        Diagnose ECLIPSE/OPM simulator crashes and QC decks before running.
        The agent holds full conversation context — each follow-up refines the fix
        without losing track of the original error.
 
        #### Steps
        1. Select **Simulator Debugger** from the top navigation.
        2. Choose **Debug Mode** (you have an error log) or **QC Mode** (proactive review).
        3. Paste your `.DATA` deck snippet in the left panel.
        4. In Debug Mode, paste the simulator error log in the right panel.
        5. Click **Diagnose Error** or **Run QC Review**.
        6. Read the diagnostic — metrics, warnings, and the proposed fix appear below.
        7. Use the **Follow-up** box to clarify, ask for an alternative fix, or
           request the agent to check other wells/sections.
        8. Tick **HITL checkbox** and export the full session or the last fix only.
 
        #### Tips
        - Even with an incomplete deck or meaningless entry like "Ranspac", the agent will respond smartly and accordingly.
        - For large decks, paste the section nearest the error rather than the full file.
        - The agent validates keyword spelling and section placement against the
          ECLIPSE / OPM  keyword database — it cannot hallucinate a
          keyword that isn't in the database.
        - Click **Clear & Start Over** between unrelated errors to avoid
          context bleed between sessions.
        """)
 
    with tab_dca:
        st.markdown("""
        #### Purpose
        Bulk Decline Curve Analysis and EUR estimation for up to 300 wells
        across 10+ fields — matching the tester's feedback for production workflow.
 
        #### CSV Format
        Upload a file with exactly these four columns:
 
        | Field | WellName | Date | OilRate |
        |-------|----------|------|---------|
        | AGBAMI | AGBAMI-001 | 2018-06-01 | 4007.1 |
 
        Use the built-in **placeholder dataset** to explore the tool without uploading data.
        A realistic 10-field / 270-well synthetic CSV is also available for scale testing.
 
        #### Steps
        1. Select **Asset Intelligence** from the top navigation.
        2. Upload your CSV or select the placeholder.
        3. Set **Economic Limit** (STB/D), **abandonment buffer**, and **forecast horizon**.
        4. Well and field results appear automatically.
        5. Use **Chart controls** to select wells and configure scatter axes.
        6. Click **Run AI Diagnosis** for the agent's anomaly interpretation.
        7. Use the **Follow-up** box to ask specific questions about the results.
        8. Export well EUR and field rollup CSVs from the Export section.
 
        #### Tips
        - The tool automatically selects the best Arps model (exponential, hyperbolic,
          or harmonic) by R² — you don't need to pre-specify the decline type.
        - Wells with **b > 1.0** are flagged — under SPE-PRMS you must use exponential
          decline for proved (1P) reserves booking; b > 1 is only valid for 2P/3P.
        - Adjust the **abandonment buffer** slider to match your operational lead time
          for workover decisions (typical onshore Nigeria: 3–6 months).
        """)
 
    with tab_relperm:
        st.markdown("""
        #### Purpose
        Generate ECLIPSE SWOF and SGOF relative permeability tables using
        Corey correlations — the standard approach when no SCAL laboratory
        data is available.
 
        #### Steps
        1. Select **RelPerm Generator** from the top navigation.
        2. Choose **Analogue / Manual** for a Niger Delta depositional analogue,
           or **Derive from k and φ** to classify rock from permeability and porosity.
        3. In k/φ mode: enter permeability (mD) and porosity (fraction) —
           the tool classifies your rock using Winland R35 and suggests Corey exponents.
        4. Adjust parameters as needed (all sliders are overridable).
        5. Click **Generate SWOF Table** — curve and ECLIPSE syntax appear immediately.
        6. Scroll to **SGOF** — set gas-oil parameters and generate.
        7. Use **SWOF + SGOF Combined** export for a single `.INC` ready for
           `INCLUDE` in your PROPS section.
        8. Click **Interpret RelPerm** for the AI's geological consistency review.
        9. Use the **Follow-up** box to ask about mixed-wet corrections, Pc effects, etc.
 
        #### Available Niger Delta analogues
        - Shallow Marine Sand (shoreface/barrier bar)
        - Fluvial/Deltaic Sand (distributary channels)
        - Deepwater Turbidite (Agbami-type)
        - Tight/Cemented Sand (deep burial)
 
        #### Tips
        - Kro_max in SGOF should match Kro_max in SWOF — large discrepancies cause
          Stone's model discontinuities and simulator convergence problems.
        - Pc = 0 is the default. For transition zones or thin reservoirs, replace
          with J-function derived values from core data.
        - Winland R35 exponents are a starting point — calibrate against production
          history when data becomes available.
        """)
 
    with tab_gov:
        st.markdown("""
        #### Purpose
        Review AI session activity, compliance status, and data governance.
 
        #### Audit Trail
        - Every AI inference is logged with timestamp, action, safety score, and provider.
        - Filter by action type, provider, or minimum score.
        - Export as CSV for post-session records or corporate compliance documentation.
 
        #### Safety Scores
        | Score | Meaning | Action required |
        |-------|---------|-----------------|
        | ≥ 80% | Acceptable | Standard review |
        | 60–79% | Review recommended | Engineer verification before use |
        | < 60% | HITL sign-off required | Do not act on output without review |
 
        #### Session Management
        - **Clear Session** removes all AI outputs and audit records from memory.
        - Exported files are unaffected — only in-session memory is cleared.
        - Download your audit trail and any exports before clearing or closing the browser.
 
        #### Data governance
        - **Zero Data Retention:** No well data or deck content is stored beyond
          the active browser session or transmitted to third parties.
        - **Regulatory refs:** SPE-PRMS (2018) · DPR Nigeria · OSPAR Decision 98/3 · ISO 13703.
 
        #### Support
        For technical assistance: **okpo.ekpenyong@gmail.com** · **info@exzing.com**
        """)

        
            
# --- PERSISTENT FOOTER DISCLAIMER ---
st.markdown("---")
st.markdown(
    """
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeeba; text-align: center;">
        <p style="color: #856404; font-size: 0.9rem; margin-bottom: 0;">
            <strong>⚠️ Engineering Disclaimer:</strong> ExzingReservoirAgent is an AI-powered technical consultant. 
            Please check all responses before use.
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Also added to the sidebar for constant visibility
   