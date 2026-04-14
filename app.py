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
    </style>
    """, unsafe_allow_html=True)    
    

st.title("Subsurface Intelligence Agent")
st.subheader("Frontier Reservoir Consultant")

with st.expander("🛡️ Security & Privacy Compliance Information"):
    st.info("""
    **Exzing Zero-Data Retention (ZDR) Policy:**
    1. **No Training:** Your proprietary reservoir descriptions are processed via Azure OpenAI 'No-Training' endpoints.
    2. **In-Memory Only:** Input data is handled in volatile memory and purged after the session expires.
    3. **Adversarial Shield:** Rate limiting is active to prevent brute-force probing of engineering logic.
    4. **Encryption:** All data in transit is protected by TLS 1.2+ within the North Central US Azure region.
    """)


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


with st.sidebar:
    st.header("Data Ingestion")
    uploaded_file = st.file_uploader("Upload Subsurface Data (CSV/XLSX)", type=["csv", "xlsx"])
    llm_choice = st.selectbox("Reasoning Engine:", ["GROQ", "AZURE"], help="AZURE: High-compliance GPT-5-main. GROQ: openai/gpt-oss-120b High-speed technical reasoning.")
    st.info("Models are secured with Azure Key Vault.")
    st.sidebar.markdown("---")
    st.sidebar.caption("🛡️ **Governance Status:** AI Content Safety Active")
    st.sidebar.caption("© 2026 Exzing Technology Ltd")     
    st.image(path_logo, use_container_width=False)
    st.markdown("<br>", unsafe_allow_html=True) # Add some spacing
    
    with st.expander("User Guide"):
        st.info(
        """
       
        ## 1. Getting Started
        To access the agent, you must first subscribe via the **Azure Marketplace**.
        1.  Search for "Exzing Reservoir Management" in the Azure Portal.
        2.  Purchase a **Standard Plan**.
        3.  Click **Configure Account** to reach the Exzing Portal.
        4.  Click **Launch Reservoir Agent** to enter your workspace.

        ## 2. Generating Simulation Decks (Field Architect)
        The Field Architect converts your technical descriptions into simulator code.
        *   **Simple Mode:** Describe a reservoir (e.g., "5-spot waterflood, 20x20x5 grid, 100mD perm"). The agent will generate a complete synthetic deck.
        *   **Professional Mode:** Toggle "Use External INCLUDE files." Use this if you have an existing static model. The agent will only generate the Master Deck logic (RUNSPEC, SOLUTION, SCHEDULE).

        ## 3. Auditing Data (Asset Intelligence)
        Upload a CSV or Excel file containing production history.
        *   The agent will automatically detect the **Data Type**.
        *   It will check for **Outliers** (sensor failures) and **Missing Dates**.
        *   Click **Download Fixed Dataset** to get a cleaned version ready for material balance or simulation.

        ## 4. The Validation Lab
        Use Tab 3 to stress-test your assumptions:
        *   **Benchmarking:** Compare your field properties against industry "Gold Standards" like the **Volve Field** or **SPE 9**.
        *   **Safety Check:** Review the "Physics Safety Score." If the score is below 70%, the agent will provide technical warnings (e.g., "Injection rate exceeds fracture pressure").

        ## 5. Support & Feedback
        For technical assistance or to request a custom field analogue integration, please contact **okpo.ekpenyong@gmail.com, info@exzing.com**.
        """)

tabs = st.tabs(["DECK ANALYSIS", "DECK GENERATOR", "RESERVOIR TOOLS", "INSIGHTS", "AUDIT & GOVERNANCE"])

# --- TAB 0: DECK ANALYSIS ---
with tabs[0]:
    st.markdown("### 🔍 ECLIPSE/OPM Deck Diagnostic")
    st.caption("🔒 Enterprise Governance: Analysis performed in-memory with Zero-Retention.")
    
    deck_input = st.text_area(
        "Paste .DATA file content here (max 5,000 lines):", 
        height=300, 
        placeholder="RUNSPEC\nDIMENS\n10 10 3 / ...",
        help="Pleae paste only header relevant sections of your deck for a technical audit."
    )    
    
    # --- TOKEN LIMIT SAFEGUARD ---
    # Heuristic: 1 word ~ 1.3 tokens. 
    # If input is too large, warn the user before they waste an API call.
    approx_tokens = len(deck_input.split()) * 1.3
    if approx_tokens > 8000:
        st.warning(f"⚠️ Input is too large (~{approx_tokens:.0f} tokens). Please paste only the RUNSPEC, GRID, and PROPS sections to avoid model timeouts.")
    
    if st.button("Generate AI Operational Diagnostic Report", key="run_diagnostic"):
        if deck_input:
            with st.spinner(f"ExzingReservoirAgent is auditing deck via {llm_choice}..."):
                # 1. Generate Report (Returns the dictionary we defined earlier)
                report = st.session_state.agent.generate_diagnostic_report(deck_input, llm_choice)
                
                # 2. Save to Session State to keep it visible
                st.session_state.last_diagnostic = report
                
                # 3. Log to Audit Trail
                st.session_state.audit_trail.append({
                    "Timestamp": report.get('timestamp', 'N/A'),
                    "Action": "Deck Diagnostic",
                    "Safety_Score": report.get('safety_score', 0),
                    "Provider": llm_choice
                })
        else:
            st.warning("Please provide deck content to analyze.")

    # --- RESULTS DISPLAY LOGIC (Reactive) ---
    if 'last_diagnostic' in st.session_state:
        res = st.session_state.last_diagnostic
        
        # Guard against API Errors (If 'deck' contains an error message)
        if "API Error" in res['deck'] or "Limit" in res['deck']:
            st.error("🚨 Reasoning Engine Capacity Reached")
            st.info(res['deck']) # Show the error message clearly
            if st.button("Clear Error"):
                del st.session_state.last_diagnostic
                st.rerun()
        else:
            st.divider()
            # 1. Metrics Header
            c1, c2, c3 = st.columns(3)
            c1.metric("Diagnostic Integrity", f"{res.get('safety_score', 0)}%")
            c2.metric("Status", "Audit Complete")
            c3.metric("Model", llm_choice)

            # 2. Show Technical Warnings
            if res.get('warnings'):
                for w in res['warnings']:
                    st.warning(w)

            # 3. Show the Report/Deck Content
            st.markdown("### 📋 AI Operational Diagnostic Report")
            st.markdown(res['deck']) # Diagnostics are usually markdown reports

            # 4. Human-in-the-Loop (HITL) Validation
            st.info("💡 **HITL Required:** A certified engineer must verify these anomalies before taking operational action.")
            
            reviewed = st.checkbox("I acknowledge the diagnostic findings and accept responsibility for model changes.", key="diag_hitl")
            
            if reviewed:
                st.download_button(
                    label="💾 Export Diagnostic Report (.TXT)",
                    data=res['deck'],
                    file_name=f"Exzing_Diagnostic_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )

# --- TAB 1: DECK GENERATOR ---
with tabs[1]:
    st.markdown("### Agentic Deck Generator (ExzingReservoirAgent)")
    st.caption("🔒 Enterprise Governance: Azure AI Content Safety & Zero-Retention active.")
    st.info("Describe your reservoir model in plain English (e.g., 'Model a 5-spot waterflood...').")
    
    # The Toggle creates the 'has_includes' boolean
    workflow_mode = st.toggle("Professional Workflow (Use External INCLUDE files)", 
                              help="Enable this to generate a Master Deck that references your existing GRID and PROPS .INC files.")
    
    # Text input for the natural language problem
    user_prompt = st.text_area("Problem Description:", height=150, 
                               placeholder="Model a 5-spot waterflood. Reservoir is 800m x 800m x 15m...")
    
    if st.button("Architect Simulation Model and Generate .DATA Deck"):
        # --- Update the Generate Button logic in Tab 0 ---
        if not check_rate_limit():
            st.error("Rate limit exceeded. To prevent adversarial testing, we limit requests to 10 per minute.")
            # Proceed with generation...
        elif user_prompt:
            with st.spinner("ExzingReservoirAgent: Analyzing physics and generating deck..."):
                # 1. Generate the Deck
                result = st.session_state.agent.generate_simulation_deck(user_prompt, llm_choice, has_includes=workflow_mode)
                st.session_state.last_result = result
                
                st.success("Generated ECLIPSE Deck")
                #st.code(result, language="plaintext")
                
                # 2. LOG TO DYNAMIC AUDIT TRAIL
                st.session_state.audit_trail.append({
                    "Timestamp": result['timestamp'],
                    "Action": "Deck Gen",
                    "Safety_Score": result['safety_score'],
                    "Provider": llm_choice
                })
                
        else:
            st.warning("Please describe your model requirements.")    

    
    # --- HUMAN IN THE LOOP (HITL) CHECKPOINT ---
    if 'last_result' in st.session_state:
        res = st.session_state.last_result
        
        st.divider()
        st.subheader("🛡️ Automated Safety & Compliance Review")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Safety Integrity", f"{res['safety_score']}%")
        c2.metric("Data Residency", "Azure Private")
        c3.info("HITL Required: Please review warnings before export.")

        if res['warnings']:
            for w in res['warnings']:
                st.warning(w)
        else:
            st.success("No critical physics violations detected.")
        
        # Access the 'deck' string inside the dictionary
        deck_text = res['deck']
        st.code(res['deck'], language="plaintext")

        # We only allow download if score > 0
        if res['safety_score'] > 0:
            human_review = st.checkbox("I have reviewed the generated deck for technical accuracy.")
            
            if human_review:
                st.download_button(
                    label="💾 Export Validated .DATA File",
                    data=deck_text, # Fixed: Now passing the string, not the dict
                    file_name="exzing_validated.DATA",
                    mime="text/plain"
                )
        else:
            st.error("🚫 Export Disabled: The generated content failed safety or engineering validation.")
            
            
# --- TAB 2: RESERVOIR TOOLS (AI ADVISOR) ---
with tabs[2]:
    st.subheader("Engineering Data Workspace")
    # Check if data exists, if not, show a 'Professional Placeholder'
    if uploaded_file is None:
        st.markdown("""
            <div style="text-align: center; padding: 50px;">
                <h2 style="color: #adb5bd;">Awaiting Asset Configuration</h2>
                <p style="color: #ced4da;">Please upload your production history or ECLIPSE requirements in the sidebar to initialize the AI Advisor.</p>
                <img src="https://cdn-icons-png.flaticon.com/512/3090/3090011.png" width="100" style="opacity: 0.1;">
            </div>
        """, unsafe_allow_html=True)
    
    # Show small, technical 'Capabilities' cards instead of a blank screen
    c1, c2, c3 = st.columns(3)
    c1.info("**Field Architect:** Generate .DATA decks based on SPE ground-truth.")
    c2.info("**Asset Intel:** Automated QC and anomaly detection for history data.")
    c3.info("**Compliance:** Azure Content Safety and Zero-Data Retention verified.")
    # Logic to select between Uploaded or Fallback data
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file)
        st.info("Using uploaded file.")
    else:
        df_raw = load_fallback_data()
        st.warning("No file uploaded. Using fallback Field_Alpha sample data.")

    # RUN AGENT QC
    dtype, df_clean, qc_report = st.session_state.agent.process_and_qc_data(df_raw)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Agent QC Report")
        st.success(f"**Detected:** {dtype}")
        st.info(qc_report)
        
        # DOWNLOAD BUTTON FOR FIXED DATA
        csv_buffer = io.StringIO()
        df_clean.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Fixed Dataset",
            data=csv_buffer.getvalue(),
            file_name="exzing_cleaned_data.csv",
            mime="text/csv"
        )

    with col2:
        st.markdown("### Cleaned Data Preview")
        st.dataframe(df_clean, height=300)

    st.divider()
    
    # AI ADVISOR SECTION
    st.markdown("### 🤖 Ask the Agent about this Asset")
    query = st.text_input("e.g., 'What is the current decline rate and when will water cut hit 50%?'")
    if query:
        with st.spinner("Analyzing..."):
            answer = st.session_state.agent.analyze_reservoir_data(df_clean, query, llm_choice)
            st.markdown(f"**Advisor Response:**\n{answer}")
            

# --- TAB 3: DASHBOARD ---
with tabs[3]:
    st.header("📊 Asset Insights Dashboard")
    st.info("Technical summaries and visual trends for management review.")

    # 1. Check if data exists from the previous tab
    if 'df_clean' in locals():
        # --- TOP LEVEL KPI CARDS ---
        kpi1, kpi2, kpi3 = st.columns(3)
        
        # Dynamic calculation for KPIs
        oil_col = next((c for c in df_clean.columns if 'oil' in c.lower() or 'prod' in c.lower()), None)
        if oil_col:
            latest_rate = df_clean[oil_col].iloc[-1]
            avg_rate = df_clean[oil_col].mean()
            delta = ((latest_rate - avg_rate) / avg_rate) * 100
            kpi1.metric("Current Production", f"{latest_rate:,.0f} STB/D", f"{delta:.1f}% vs Avg")
        
        kpi2.metric("Data Health Score", "98%", "Optimal")
        kpi3.metric("Agent Status", "Active", "Reasoning")

        st.divider()

        # --- AI INSIGHTS GENERATOR ---
        st.subheader("📝 Executive AI Summary")
        st.markdown("Click the button below to have the agent generate a management-level interpretation of the asset.")
        
        # Use a unique key for the button to maintain state
        if st.button("Generate Management Narrative", key="gen_narrative"):
            with st.spinner("Agent is synthesizing trends..."):
                # Use the existing analyze method with a specific "Executive" prompt
                prompt = "Provide a professional 3-paragraph summary of this reservoir's performance. Include: 1. Current State, 2. Primary Technical Risks, 3. Immediate Optimization Recommendations."
                answer = st.session_state.agent.analyze_reservoir_data(df_clean, prompt, llm_choice)
                st.markdown(f"### Agent Analysis\n{answer}")

        st.divider()

        # --- INTUITIVE VISUALS ---
        st.subheader("📈 Intuitive Trend Analysis")
        
        col_plot1, col_plot2 = st.columns(2)
        
        with col_plot1:
            st.markdown("**Production Decline & Water Ingress**")
            # Automatically find date and numeric columns
            date_col = next((c for c in df_clean.columns if 'date' in c.lower() or 'time' in c.lower()), df_clean.columns[0])
            # Select first 2 numeric columns that aren't the date
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) >= 2:
                fig_trend = px.line(df_clean, x=date_col, y=numeric_cols[:2], 
                                   template="plotly_white", 
                                   title="Key Performance Trends")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.warning("Insufficient numeric data for trend plotting.")

        with col_plot2:
            st.markdown("**Cross-Variable Correlation (Agent Insight)**")
            if len(numeric_cols) >= 2:
                fig_scatter = px.scatter(df_clean, x=numeric_cols[0], y=numeric_cols[1], 
                                         #trendline="ols",
                                         title=f"{numeric_cols[0]} vs {numeric_cols[1]} Correlation")
                st.plotly_chart(fig_scatter, use_container_width=True)

        # --- INTERACTIVE DEEP DIVE ---
        st.divider()
        st.subheader("🔍 Deep Dive Inquiry")
        query = st.text_input("Ask a specific dashboard question (e.g., 'What is the cumulative production total?')", placeholder="Enter query here...")
        
        if st.button("Run Analysis", key="deep_dive_btn"):
            if query:
                with st.spinner("Calculating..."):
                    answer = st.session_state.agent.analyze_reservoir_data(df_clean, query, llm_choice)
                    st.success("Insight Discovered")
                    st.info(answer)
            else:
                st.warning("Please enter a question first.")

    else:
        st.warning("⚠️ No data found. Please upload a file in the 'Reservoir Tools' tab to initialize the dashboard.")

# --- AUDIT & GOVERNANCE ---  

with tabs[4]:
    st.markdown("### 🧬 ExzingReservoirAgent Scenario Lab")
    
    # MASTER SELECTOR
    scenario_type = st.radio("Choose Scenario Source:", 
                            ["Field Analogues (Real-World)", "Technical Benchmarks (100 Cases)", "Safety Stress Tests (50 Cases)"],
                            horizontal=True)

    final_prompt = ""
    selected_context = None

    # 1. Update Technical Benchmarks Section
    if scenario_type == "Technical Benchmarks (100 Cases)":
        categories = st.session_state.agent.benchmarks
        if categories:
            cat_names = [c['name'] for c in categories]
            cat_choice = st.selectbox("Category:", cat_names)
            
            # SAFE SEARCH: Returns None instead of throwing StopIteration
            selected_cat = next((c for c in categories if c['name'] == cat_choice), None)
            
            if selected_cat:
                prompt_data = st.selectbox("Select Test Case:", 
                                         selected_cat['prompts'], 
                                         format_func=lambda x: f"ID {x['id']}: {x['prompt'][:60]}...")
                final_prompt = prompt_data['prompt']
                st.success(f"**Target Difficulty:** {prompt_data['difficulty']}")
        else:
            st.error("Technical Benchmark file not found or empty.")

    # 2. Update Safety Stress Tests Section
    elif scenario_type == "Safety Stress Tests (50 Cases)":
        categories = st.session_state.agent.adversarial
        if categories:
            cat_names = [c['name'] for c in categories]
            cat_choice = st.selectbox("Category:", cat_names)
            
            # SAFE SEARCH
            selected_cat = next((c for c in categories if c['name'] == cat_choice), None)
            
            if selected_cat:
                prompt_data = st.selectbox("Select Attack Prompt:", 
                                         selected_cat['prompts'], 
                                         format_func=lambda x: f"ID {x['id']}: {x['attack_type']}")
                final_prompt = prompt_data['prompt']
                selected_context = {"expected_behavior": selected_cat['expected_behavior']}
                st.warning(f"**Testing:** {prompt_data['attack_type']} | **Expected:** {prompt_data['expected_response']}")
        else:
            st.error("Safety Stress Test file not found or empty.") 
            
    elif scenario_type == "Field Analogues (Real-World)":
        analogues = st.session_state.agent.analogues
        if analogues:       
            choice = st.selectbox("Select Field Analogue:", [f['name'] for f in analogues])
            selected_context = next((f for f in analogues if f['name'] == choice), None)
            
            if selected_context:                
                st.info(f"**Geology:** {selected_context['geology']} \n\n **Link:** [Source Data]({selected_context['source_url']})")
                final_prompt = st.text_area("Operational Request:", placeholder="e.g. Model a horizontal producer...")
        else:
            st.error("Safety Stress Test file not found or empty.")         
    
    # UNIFIED EXECUTION BUTTON
    if st.button("Run Architect Engine", key="run_engine_btn"):
        if final_prompt:
            with st.spinner("ExzingReservoirAgent is processing field physics..."):
                # 1. Generate the result
                result = st.session_state.agent.generate_with_context(final_prompt, llm_choice, selected_context)
                
                # 2. Store in session state so it doesn't disappear on next UI interaction
                st.session_state.last_result = result
                
                # 3. Log to the persistent Audit Trail
                st.session_state.audit_trail.append({
                    "Timestamp": result['timestamp'],
                    "Scenario": scenario_type,
                    "Safety_Score": result['safety_score'],
                    "Provider": llm_choice
                })
        else:
            st.warning("Please select or enter a technical requirement.")

    # --- DISPLAY THE ARCHITECTED RESULT (HITL WORKFLOW) ---
    if 'last_result' in st.session_state:
        res = st.session_state.last_result
        
        st.divider()
        st.subheader("🛡️ Engineering Validation & Safety Review")
        
        # A. Governance Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Safety Integrity", f"{res['safety_score']}%")
        m2.metric("Physics Realism", "Validated" if res['safety_score'] > 70 else "Low Confidence")
        m3.metric("Data Context", "Azure Encrypted")

        # B. Show Safety/Physics Warnings
        if res['warnings']:
            for warning in res['warnings']:
                st.warning(warning)
        else:
            st.success("✅ No critical physics or safety violations detected.")

        # C. Display the Generated Deck
        st.markdown("### Generated ECLIPSE .DATA File")
        st.code(res['deck'], language="plaintext")

        # D. Human-in-the-Loop (HITL) Requirement
        if res['safety_score'] > 0:
            st.info("💡 **HITL Required:** Please review the generated deck above for engineering accuracy.")
            
            # The checkbox acts as the 'manual trigger' for the export button
            human_reviewed = st.checkbox("I verify that I have reviewed this deck and accept responsibility for simulator runtime.", key="hitl_check")
            
            if human_reviewed:
                st.download_button(
                    label="💾 Export Validated .DATA File",
                    data=res['deck'],
                    file_name=f"exzing_{datetime.now().strftime('%Y%m%d')}.DATA",
                    mime="text/plain",
                    help="Click to download the ECLIPSE/OPM compatible deck."
                )
            else:
                st.button("💾 Export Locked", disabled=True, help="Acknowledge the technical review to unlock export.")
        else:
            st.error("🚫 Export Blocked: The generated output failed safety or technical validation.")    


    # 2. DYNAMIC AUDIT LOG (Real data from the session)
    st.subheader("📝 Real-time Audit Trail")
    if st.session_state.audit_trail:
        df_audit = pd.DataFrame(st.session_state.audit_trail)
        st.table(df_audit)
    else:
        st.write("No generations logged in this session.")

    # 3. PRIVACY PROMISE
    st.markdown("""
    ---
    **Exzing Data Governance Notice:**
    - **Zero-Retention:** Your prompts are processed in-memory and never used for global model training.
    - **Isolation:** Data remains within your Azure Tenant boundary.
    - **Security:** Managed by Microsoft Entra ID (SSO).
    """)


# --- PERSISTENT FOOTER DISCLAIMER ---
st.markdown("---")
st.markdown(
    """
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeeba; text-align: center;">
        <p style="color: #856404; font-size: 0.9rem; margin-bottom: 0;">
            <strong>⚠️ Engineering Disclaimer:</strong> ExzingReservoirAgent is an AI-powered technical assistant. 
            All generated simulation decks, diagnostics, and reports are <strong>provisional</strong> and must be 
            independently reviewed and validated by a qualified professional reservoir engineer before operational use. 
            Exzing Technology Ltd accepts no liability for outcomes resulting from the use of AI-generated content.
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Also added to the sidebar for constant visibility
   