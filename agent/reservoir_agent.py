from ..qc.rules import run_qc
from ..rag.simply_rag import SimpleRAG

class ReservoirAgent:
    """
    Core reasoning engine.
    For now:
    - Runs QC
    - Retrieves from RAG
    - Plans suggestions
    """

    def __init__(self):
        self.rag = SimpleRAG()

    def load_background_docs(self, docs: dict):
        for name, text in docs.items():
            self.rag.index(name, text)

    def analyze_deck(self, parser):
        sections = parser.extract_sections()
        qc_issues = run_qc(parser.content, sections)

        plan = self.generate_plan(qc_issues, sections)

        return {
            "sections": list(sections.keys()),
            "qc_issues": qc_issues,
            "plan": plan
        }

    def generate_plan(self, issues, sections):
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
