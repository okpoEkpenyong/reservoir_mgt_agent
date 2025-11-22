from ..qc.rules import run_qc
from ..rag.simply_rag import SimpleRAG
from .llm import LLMEngine
from ..qc.advanced_rules import qc_initial_pressure, qc_pvt_completeness, qc_compdat
from ..rag.vector_store import VectorStore

class ReservoirAgent:
    """
    Core reasoning engine.
    For now:
    - Runs QC
    - Retrieves from RAG
    - Plans suggestions
    """
        
    def __init__(self, llm: LLMEngine):
        self.llm = llm
        self.memory = VectorStore()
        self.rag = SimpleRAG()
tus
    def analyze_deck(self, parser):
        sections = parser.extract_sections()

        qc_issues = []
        qc_issues += run_qc(parser.content, sections)
        qc_issues += qc_initial_pressure(sections)
        qc_issues += qc_pvt_completeness(sections)
        qc_issues += qc_compdat(sections)

        context = "\n".join(qc_issues)
        plan = self.llm.ask(
            "You are a senior reservoir engineer. Provide a recommended action plan.",
            context=context
        )

        return {
            "sections": list(sections.keys()),
            "qc_issues": qc_issues,
            "recommended_plan": plan
        }        

    def load_background_docs(self, docs: dict):
        for name, text in docs.items():
            self.rag.index(name, text)

    def generate_plan(self, issues, _sections=None):
        plan = []

        if not issues:
            plan.append("Input deck passed QC. Ready for simulation.")
            return plan

        for issue in issues:
            if "WELSPECS" in issue:
                plan.append("Verify well definitions and coordinate locations.")
            if "END" in issue:
                plan.append("Add END keyword at bottom of deck.")

        return plan
