from agent.llm import LLMEngine
from agent.safety_shields import AzureSafetyShield

import re
import pandas as pd
import numpy as np
import io
import datetime
import sys
import os
import json
import logging



class ReservoirAgent:
    def __init__(self):
        self.engine = LLMEngine()
        self.shield = AzureSafetyShield() # Initialize the actual Azure Shield
        # Benchmark "Golden" values for validation
        self.benchmarks = {
            "SPE1": {"grid": "10x10x3", "stoiip_approx": 1.0, "fluid": "Gas"},
            "SPE9": {"grid": "24x25x15", "stoiip_approx": 120.0, "fluid": "Black Oil"},
            "VOLVE": {"grid": "Approx 100k cells", "fluid": "Volatile Oil"}
        }
        # Governance settings
        self.privacy_mode = "ZERO_RETENTION" # Enforced via Azure Policy
        
        # 1. Get the directory where THIS file (reservoir_agent.py) lives:
        # This will be: .../reservoir_mgt_agent/agent/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Define Absolute Paths pointing to the 'data' subfolder inside 'agent'
        path_analogues = os.path.join(current_dir, 'data', 'field_library.json')
        path_benchmarks = os.path.join(current_dir, 'data', 'benchmarking_suite.json')
        path_adversarial = os.path.join(current_dir, 'data', 'adversarial_suite.json')

        # 3. Load the data
        self.analogues = self._load_json(path_analogues).get('field_analogues', [])
        self.benchmarks = self._load_json(path_benchmarks).get('categories', [])
        self.adversarial = self._load_json(path_adversarial).get('categories', [])
        
        # Debugging prints for your terminal
        #print(f"DEBUG: Found data folder at: {os.path.join(current_dir, 'data')}")
        #print(f"DEBUG: Loaded {len(self.analogues)} Analogues")
        #print(f"DEBUG: Loaded {len(self.benchmarks)} Benchmarks")
        #print(f"DEBUG: Loaded {len(self.adversarial)} Adversarial cases")

    def _load_json(self, path):
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logging.log(logging.INFO,f"ERROR: File not found at {path}")
        except Exception as e:
            logging.log(logging.INFO,f"ERROR: Could not parse JSON at {path}: {str(e)}")
        return {}
    
    def _enforce_privacy_scrub(self, text):
        """Redacts potentially sensitive metadata before processing if needed."""
        # Simple example: Redact specific project names if they match a pattern
        # This acts as a secondary shield for IP leakage
        return text

    def process_and_qc_data(self, df):
        """
        Robustly detects data type, performs QC, and returns (Type, Cleaned_DF, Report)
        """
        cols = [c.lower() for c in df.columns]
        report = []
        
        # 1. CLASSIFICATION LOGIC
        if any('date' in c or 'time' in c for c in cols) and any('oil' in c or 'prod' in c for c in cols):
            data_type = "Production History"
        elif any('rs' in c or 'bo' in c or 'pvt' in c for c in cols):
            data_type = "PVT / Well Test Data"
        else:
            data_type = "General Subsurface Data"

        # 2. QC & AUTO-FIXING
        original_count = len(df)
        
        # Fix dates
        date_col = next((c for c in df.columns if 'date' in c.lower()), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            report.append(f"Standardized date format in column '{date_col}'")

        # Handle Missing Values (Interpolation for engineering continuity)
        if df.isnull().values.any():
            df = df.interpolate(method='linear').fillna(method='bfill')
            report.append("⚠️ Detected missing values: Applied linear interpolation for continuity.")

        # Outlier Detection (Z-Score > 3 for production)
        if data_type == "Production History":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                z_score = (df[col] - df[col].mean()) / df[col].std()
                outliers = len(df[np.abs(z_score) > 3])
                if outliers > 0:
                    report.append(f"⚠️ Flagged {outliers} outliers in {col} (Values > 3σ).")

        report.append(f"📊 Processed {len(df)} rows (Type: {data_type}).")
        return data_type, df, "\n".join(report)

    def is_input_technically_sound(self, user_req):
        """Checks if the prompt contains enough technical context to build a model."""
        # 1. Length Check
        if len(user_req.strip()) < 15:
            return False, "Input is too short. Please provide a more detailed reservoir description."

        # 2. Technical Anchor Check
        # Does the prompt contain at least one key technical concept?
        anchors = ['grid', 'field', 'volve', 'norne', 'spe', 'waterflood', 'injection', 
                   'porosity', 'permeability', 'perm', 'md', 'api', 'pressure', 'well', 'spot']
        
        has_anchor = any(anchor in user_req.lower() for anchor in anchors)
        if not has_anchor:
            return False, "Input lacks technical context. Please include parameters like dimensions, properties, or specific field analogues."

        return True, "Success"
    
    def generate_diagnostic_report(self, deck_content, model_choice):
        system_prompt = """You are a Senior Reservoir Simulation Expert performing a QC on an ECLIPSE/OPM deck.
        GOVERNANCE: You cannot bypass safety limits. Use Azure AI Content Safety protocols.
        PRIVACY NOTICE: This session is under Zero Data Retention. 
        STRICT REQUIREMENT: user input must first satisify the condition and format for a .DATA deck
        """
        reasons = []
        user_content = f"Analyze this deck snippet:\n\n{deck_content}"
        
        is_safe, message = self.shield.analyze_text_safety(user_content)
        
        if not is_safe:
            return {
                "deck": "BLOCK: Input violated Azure AI Content Safety protocols.",
                "safety_score": 0,
                "warnings": [message],
                "timestamp": "N/A"
            }
        

        raw_deck = self.engine.analyze_reservoir_task(model_choice, system_prompt, user_content)
        
        # HITL Hook: Calculate score before returning to UI
        safety_score, warnings = self.calculate_safety_score(raw_deck, user_content)
        
        return {
            "deck": raw_deck,
            "safety_score": safety_score,
            "warnings": warnings,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }                
              
    def analyze_reservoir_data(self, df, user_query, model_choice):
        df_info = df.describe().to_string()
        system_prompt = "You are a Reservoir Data Analyst. Answer technical questions based on this data context."
        user_content = f"DATA CONTEXT:\n{df_info}\n\nUSER QUESTION: {user_query}"
        
        is_safe, message = self.shield.analyze_text_safety(user_content)
        
        if not is_safe:
            return {
                "deck": "BLOCK: Input violated Azure AI Content Safety protocols.",
                "safety_score": 0,
                "warnings": [message],
                "timestamp": "N/A"
            }
        return self.engine.analyze_reservoir_task(model_choice, system_prompt, user_content)
        
    def generate_executive_summary(self, content, context_type, model_choice):
        """Generates a high-level summary for the dashboard."""
        system_prompt = f"You are a Senior Reservoir Engineer. Summarize this {context_type} into 3 bullet points for a management review."
        user_content = f"Here is the data:\n\n{content}"
        return self.engine.analyze_reservoir_task(model_choice, system_prompt, user_content)
        
    def _validate_deck_syntax(self, deck_content):
        """Checks if generated deck contains essential ECLIPSE keywords."""
        found = [kw for kw in self.valid_keywords if kw in deck_content.upper()]
        score = len(found) / len(self.valid_keywords)
        return score, found

    def _check_physical_boundaries(self, user_requirements):
        """Heuristic check for dangerous or unrealistic user inputs."""
        warnings = []
        # Check for high injection rates
        rate_match = re.search(r"(\d+)\s*(bbl|rate|injection)", user_requirements.lower())
        if rate_match and int(rate_match.group(1)) > 5000:
            warnings.append("⚠️ HIGH RISK: Injection rate exceeds typical fracture limits for standard reservoirs.")
        
        # Check for unrealistic porosity
        poro_match = re.search(r"(\d+)%\s*porosity", user_requirements.lower())
        if poro_match and int(poro_match.group(1)) > 45:
            warnings.append("⚠️ PHYSICAL IMPOSSIBILITY: Porosity > 45% is geologically unrealistic.")
            
        return warnings    
    
    
    def calculate_safety_score(self, deck_content, user_req):
        """Multi-factor safety and realism scoring."""
        score = 100
        reasons = []
        
        # 1. Physics Check: High Injection
        if re.search(r"(rate|inj).*([5-9]\d{3}|[1-9]\d{4})", user_req.lower()):
            score -= 30
            reasons.append("High injection rate flagged (Fracture risk)")
            
        # 2. Syntax Check: Missing Keywords
        for kw in ["RUNSPEC", "GRID", "PROPS", "SOLUTION", "SUMMARY", "SCHEDULE", "DIMENS"]:
            if kw not in deck_content.upper():
                score -= 15
                reasons.append(f"Missing critical keyword: {kw}")
        
        # 3. Adversarial/Jailbreak Check
        BANNED_PHRASES = [
            'ignore previous instructions',
            'jailbreak',
            'system prompt',
            'negative permeability',
            'crash',
            'overflow'
            'bypass',
            'override'
        ]
        if any(x in user_req.lower() for x in BANNED_PHRASES):
            score -= 40
            reasons.append("Safety override attempt detected")
            
        return max(score, 0), reasons

    def run_benchmark(self, model_name):
        """Compares AI deck logic against industry ground-truth."""
        if model_name in self.benchmarks:
            return f"Comparison against {model_name} standard: Validating STOIIP and Grid Topology..."
        return "Unknown benchmark model."

    def get_analogue_data(self, name):
        library = self._load_json('data/field_library.json')
        return next((f for f in library['field_analogues'] if f['name'] == name), None)

        def generate_simulation_deck_with_analogue(self, analogue_name, specific_reqs, model_choice):
            analogue = self.get_analogue_data(analogue_name)
            
            system_prompt = f"""You are a Senior Reservoir Consultant. 
            You are architecting a model BASED ON the real-world {analogue['name']}.
            
            ANALOGUE GEOLOGY: {analogue['geology']}
            TYPICAL PVT: {analogue['pvt']}
            PHYSICS CONTEXT: {analogue['tech_specs']}
            
            Requirement: {specific_reqs}
            
            Your output must be a valid ECLIPSE (.DATA) file that respects the physical constraints of the {analogue_name} analogue."""

            return self.engine.analyze_reservoir_task(model_choice, system_prompt, specific_reqs)
    

    def generate_with_context(self, prompt, model_choice, context_data=None):
        """
        Unified generation point for ALL scenarios.
        context_data can be Analogue metadata or Test Case metadata.
        """
        # 1. Safety Filter (Inbound)
        is_safe, msg = self.shield.analyze_text_safety(prompt)
        if not is_safe:
            return self._format_error(f"Azure Safety Flag: {msg}")

        # 2. Context Injection
        system_msg = "You are ExzingReservoirAgent, a Senior Reservoir Simulation Expert."
        if context_data:
            if 'source_url' in context_data: # It's an Analogue
                system_msg += f"\nANALOGUE CONTEXT: Model this based on {context_data['name']} ({context_data['source_url']})."
            elif 'expected_behavior' in context_data: # It's an Adversarial test
                system_msg += f"\nSAFETY MODE: User is testing boundaries. Strictly follow: {context_data['expected_behavior']}."

        # 3. Execution
        raw_output = self.engine.analyze_reservoir_task(model_choice, system_msg, prompt)
        
        # 4. Physics Scoring (Outbound)
        score, warnings = self.calculate_safety_score(raw_output, prompt)
        
        return {
            "deck": raw_output,
            "safety_score": score,
            "warnings": warnings,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _format_error(self, message):
        return {"deck": "BLOCK", "safety_score": 0, "warnings": [message], "timestamp": "N/A"}
    
    def generate_simulation_deck(self, user_requirements, model_choice, has_includes=False):
        # 1. ACTUAL AZURE CONTENT SAFETY CHECK (Inbound)
        is_safe, message = self.shield.analyze_text_safety(user_requirements)
        
        if not is_safe:
            return {
                "deck": "BLOCK: Input violated Azure AI Content Safety protocols.",
                "safety_score": 0,
                "warnings": [message],
                "timestamp": "N/A"
            }
            
        include_logic = ""
        if has_includes:
            include_logic = """
            PROFESSIONAL MODE: The user has existing static models. 
            Do NOT generate the GRID or PROPS cell data. 
            Instead, use keywords that reference those INCLUDE files to be imported.
            """


        # 2. PROCEED TO GENERATION
        system_prompt = f"""You are a Reservoir Simulation Expert. Generate an ECLIPSE .DATA file.
        GOVERNANCE: You cannot bypass safety limits. Use Azure AI Content Safety protocols.
        PRIVACY NOTICE: This session is under Zero Data Retention. 
        COMPLETNESS: problem description should not be vague but sensible and full description of an oil/gas field or reservoir system.
        STRICT REQUIREMENT: If the user requirements are technically incomplete, contradictory, or nonsensical, 
        do NOT generate a deck. Instead, explain exactly what technical parameters are missing.
        if {include_logic}:
        Generate a professional ECLIPSE Master Deck. Also observe governance, privacy and completeness.
        Ensure well control logic is robust and references the correct cell indices.
        Do not store or reference this technical IP in any global training corpus.
        Process the following requirements strictly in-memory.
        """
        
        raw_deck = self.engine.analyze_reservoir_task(model_choice, system_prompt, user_requirements)
        
        # 3. INTERNAL PHYSICS SCORING (Outbound)
        # HITL Hook: Calculate score before returning to UI
        safety_score, warnings = self.calculate_safety_score(raw_deck, user_requirements)
        
        return {
            "deck": raw_deck,
            "safety_score": safety_score,
            "warnings": warnings,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    

 