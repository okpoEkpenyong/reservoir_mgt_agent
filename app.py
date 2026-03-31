import streamlit as st
from agent.reservoir_agent import ReservoirAgent

st.set_page_config(page_title="Exzing Reservoir Agent", layout="wide")

if 'agent' not in st.session_state:
    st.session_state.agent = ReservoirAgent()

st.title("🚀 Subsurface Intelligence Agent")

# Sidebar Configuration
with st.sidebar:
    model_choice = st.selectbox("Select Reasoning Model:", 
                              ["Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen3.5-397B-A17B"])
    
    # Debug info for you (remove later for security)
    token_status = "Unset"
    import os
    t = os.getenv("HF_TOKEN")
    if t:
        token_status = "Resolved ✅" if not t.startswith("@Microsoft") else "Resolving... ⏳"
    st.info(f"Key Vault Status: {token_status}")

# Logic
deck_input = st.text_area("Paste ECLIPSE .DATA content:", height=200)
if st.button("Generate Diagnostic Report"):
    with st.spinner("Agent is thinking..."):
        report = st.session_state.agent.generate_diagnostic_report(deck_input, model_choice)
        st.markdown(report)
