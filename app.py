import streamlit as st
from agent.reservoir_agent import ReservoirAgent
import pandas as pd
import io
import time

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

if 'agent' not in st.session_state:
    st.session_state.agent = ReservoirAgent()

st.title("Subsurface Intelligence Agent")
st.subheader("🤖 Frontier Reservoir Consultant")

with st.sidebar:
    st.header("Data Ingestion")
    uploaded_file = st.file_uploader("Upload Subsurface Data (CSV/XLSX)", type=["csv", "xlsx"])
    llm_choice = st.selectbox("Reasoning Engine:", ["GROQ", "AZURE"])
    st.info("Models are secured with Azure Key Vault.")

tabs = st.tabs(["Deck Analysis", "Reservoir Tools", "Insights Dashboard"])

# --- TAB 0: DECK ANALYSIS ---
with tabs[0]:
    st.markdown("### ECLIPSE/OPM Deck Diagnostic")
    deck_input = st.text_area("Paste .DATA file content here:", height=300, placeholder="RUNSPEC\nDIMENS\n10 10 3 / ...")    
    
    if st.button("Generate AI Operational Diagnostic Report"):
        if deck_input:
            with st.spinner(f"Agent is analyzing via {llm_choice}..."):
                report = st.session_state.agent.generate_diagnostic_report(deck_input, llm_choice)
                st.success("Diagnostic Report Generated")
                st.markdown(f"--- \n {report}")

            st.success(f"Done!")  
        else:
            st.warning("Please provide deck content to analyze.")

# --- TAB 1: RESERVOIR TOOLS (AI ADVISOR) ---
with tabs[1]:
    st.subheader("📊 Engineering Data Workspace")
    
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
            

# --- TAB 2: DASHBOARD ---
import plotly.express as px
import numpy as np

with tabs[2]:
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