from .llm import LLMEngine

class ReservoirAgent:
    def __init__(self):
        self.engine = LLMEngine()

    def generate_diagnostic_report(self, deck_content, model_choice):
        system_prompt = """You are a Senior Reservoir Simulation Expert. 
        Your task is to perform a Quality Control (QC) check on an ECLIPSE/OPM simulation deck.
        
        CRITICAL CHECKS:
        1. GRID: Verify dimensions and property consistency (PORO, PERM).
        2. PROPS: Check PVT ranges (PVTO, PVTW) for physical realism.
        3. SOLUTION: Ensure initial pressures and saturations are realistic.
        4. SCHEDULE: Validate well specifications (WELSPECS) and control keywords.
        
        Format your response as a professional 'Operational Diagnostic Report' with:
        - EXECUTIVE SUMMARY
        - TECHNICAL ANOMALIES FOUND
        - DIRECTIVE/ACTION PLAN"""

        user_content = f"Please analyze the following ECLIPSE deck snippet and provide a 3-step diagnostic:\n\n{deck_content}"
        
        return self.engine.analyze_reservoir_task(model_choice, system_prompt, user_content)
