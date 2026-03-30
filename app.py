import streamlit as st
import os
from agent.llm import LLMEngine
from agent.tools import calculate_arps_decline

st.set_page_config(page_title="Exzing Reservoir Agent", page_icon="🛢️", layout="wide")

# Initialize Engine
@st.cache_resource
def get_agent():
    return LLMEngine()

engine = get_agent()

st.sidebar.title("Exzing Reservoir Agent")
st.sidebar.success(f"Active Model: {engine.provider}")
st.sidebar.info(f"ID: {engine.model}")

menu = st.sidebar.radio("Navigation", ["Dashboard", "AI Advisor", "Settings"])

if menu == "Dashboard":
    st.title("🚀 Reservoir Forecast")
    qi = st.number_input("Initial Rate", value=500)
    df = calculate_arps_decline(qi, 0.05, 0.5, 24)
    st.line_chart(df.set_index("Month"))

elif menu == "AI Advisor":
    st.title("🤖 AI Reservoir Advisor")
    prompt = st.text_input("Technical Query:")
    if prompt:
        with st.spinner(f'Consulting {engine.model}...'):
            response = engine.ask(prompt)
            st.markdown(response)

elif menu == "Settings":
    st.title("⚙️ System Status")
    st.write(f"**Provider:** {engine.provider}")
    st.write(f"**Model Path:** {engine.model}")
