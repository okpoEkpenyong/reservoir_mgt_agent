import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Exzing Reservoir Agent", page_icon="🛢️", layout="wide")

# --- CUSTOM CSS FOR BRANDING ---
#st.markdown("""
#  .main { background-color: #f5f7f9; }
#    .stButton>button { background-color: #0078d4; color: white; border-radius: 5px; }
#    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
#    </style>
#    """, unsafe_content_as_True=True)

# --- SIDEBAR / BRANDING ---
st.sidebar.image("https://via.placeholder.com/150?text=Exzing+Tech", width=100) # Replace with your logo later
st.sidebar.title("Exzing Reservoir Agent")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Data Analysis", "AI Agent Advisor", "Settings"])

# --- MOCK DATA FOR THE MVP ---
def get_mock_data():
    dates = pd.date_range(start="2023-01-01", periods=12, freq='M')
    data = pd.DataFrame({
        'Date': dates,
        'Oil_Production': [500, 480, 465, 450, 430, 415, 400, 385, 370, 355, 340, 325],
        'Water_Cut': [5, 6, 8, 10, 12, 15, 18, 22, 25, 28, 32, 35],
        'Pressure': [3200, 3150, 3100, 3050, 3000, 2950, 2900, 2850, 2800, 2750, 2700, 2650]
    })
    return data

# --- MAIN CONTENT ---
if menu == "Dashboard":
    st.title("🚀 Reservoir Performance Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Production", "410 bbl/d", "-2%")
    col2.metric("Current Pressure", "2650 psi", "-50 psi")
    col3.metric("Water Cut", "35%", "+3%")
    col4.metric("Active Wells", "12", "Stable")

    df = get_mock_data()
    fig = px.line(df, x='Date', y='Oil_Production', title="Oil Production Forecast (DCA)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

elif menu == "Data Analysis":
    st.title("📊 Subsurface Data Analysis")
    uploaded_file = st.sidebar.file_uploader("Upload your Reservoir Data (CSV or Excel)", type=["csv", "xlsx"])
    #uploaded_file = st.sidebar.file_uploader("Upload VFP Data (THP, FlowRate, BHP)", type="csv")
    if uploaded_file:
        st.success("File uploaded successfully!")
        # Your actual reservoir logic would go here
    else:
        st.info("Please upload a file to begin analysis. Using sample data below.")
        st.table(get_mock_data().head())

elif menu == "AI Agent Advisor":
    st.title("🤖 AI Reservoir Advisor")
    st.markdown("Ask your reservoir agent questions about your asset performance.")
    
    prompt = st.text_input("Ask the Agent (e.g., 'What is the remaining recoverable reserve?')")
    if prompt:
        with st.spinner('Analyzing reservoir models...'):
            # This is where your back-end 'reservoir_mgt_agent' logic plugs in
            st.write(f"**Agent Response:** Based on current decline curves and pressure data, the estimated ultimate recovery (EUR) for this asset is 2.4 MMbbl.")

elif menu == "Settings":
    st.title("⚙️ Account & Subscription")
    st.write("Logged in as: **okpo.ekpenyong@gmail.com**")
    st.write("Subscription Plan: **Standard Plan**")
    st.write("Status: **Active**")