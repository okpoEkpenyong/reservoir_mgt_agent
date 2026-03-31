import streamlit as st
from agent.reservoir_agent import ReservoirAgent

st.set_page_config(page_title="Exzing Reservoir Agent", layout="wide")

# Persistent Agent Instance
if 'agent' not in st.session_state:
    st.session_state.agent = ReservoirAgent()

st.title("🚀 Subsurface Intelligence Agent")
st.subheader("🤖 Frontier Reservoir Consultant (Agentic QC)")

# Sidebar for Model Selection
with st.sidebar:
    st.header("Model Configuration")
    llm_choice = st.selectbox("Select Reasoning Model:", 
                              ["Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen3.5-397B-A17B", "mistralai/Mixtral-8x7B-Instruct-v0.1"])
    
    st.markdown("---")
    st.info("Agent is connected to Azure Key Vault for HF Token security.")

# Main Workflow
tabs = st.tabs(["Deck Analysis", "Reservoir Tools", "Dashboard"])

with tabs[0]:
    st.markdown("### ECLIPSE/OPM Deck Diagnostic")
    deck_input = st.text_area("Paste .DATA file content here:", height=300, placeholder="RUNSPEC\nDIMENS\n10 10 3 / ...")
    
    if st.button("Generate AI Operational Diagnostic Report"):
        if deck_input:
            with st.spinner(f"Agent is analyzing via {llm_choice}..."):
                report = st.session_state.agent.generate_diagnostic_report(deck_input, llm_choice)
                st.success("Diagnostic Report Generated")
                st.markdown(f"--- \n {report}")
        else:
            st.warning("Please provide deck content to analyze.")

with tabs[1]:
    st.write("Additional Reservoir Engineering tools (DCA, MBAL) will be accessible here.")

with tabs[2]:
    st.metric("Decks Analyzed", 14, "+2 today")
    st.metric("Anomalies Detected", 42, "Critical")
