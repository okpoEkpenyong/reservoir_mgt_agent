import streamlit as st
from reservoir_mgt_agent.parsers.deck_parser import DeckParser
from reservoir_mgt_agent.agent.reservoir_agent import ReservoirAgent
from reservoir_mgt_agent.agent.llm import LLMEngine

st.title("Reservoir Engineering Agent")

uploaded = st.file_uploader("Upload ECLIPSE Deck (.DATA)", type=["DATA", "txt"])

if uploaded:
    content = uploaded.read().decode("utf-8")
    with open("tmp.DATA", "w") as f:
        f.write(content)

    parser = DeckParser("tmp.DATA")

    llm = LLMEngine(
        api_key=st.secrets["AZURE_KEY"],
        endpoint=st.secrets["AZURE_ENDPOINT"],
        deployment=st.secrets["AZURE_DEPLOYMENT"]
    )

    agent = ReservoirAgent(llm)
    result = agent.analyze(parser)

    st.subheader("QC Issues")
    st.write(result["qc_issues"])

    st.subheader("Recommended Action Plan")
    st.write(result["recommended_plan"])
