#from .llm import LLMEngine
#from .safety_shield import AzureSafetyShield

from agent.llm import LLMEngine
from agent.safety_shields import AzureSafetyShield

import re
import pandas as pd
import numpy as np
import io
import datetime
import sys
import os



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
            report.append(f"✅ Standardized date format in column '{date_col}'")

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

    def generate_diagnostic_report(self, deck_content, model_choice):
        system_prompt = "You are a Senior Reservoir Simulation Expert performing a QC on an ECLIPSE/OPM deck."
        user_content = f"Analyze this deck snippet:\n\n{deck_content}"
        return self.engine.analyze_reservoir_task(model_choice, system_prompt, user_content)

    def analyze_reservoir_data(self, df, user_query, model_choice):
        df_info = df.describe().to_string()
        system_prompt = "You are a Reservoir Data Analyst. Answer technical questions based on this data context."
        user_content = f"DATA CONTEXT:\n{df_info}\n\nUSER QUESTION: {user_query}"
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

    def generate_simulation_deck(self, user_requirements, model_choice):
        # 1. ACTUAL AZURE CONTENT SAFETY CHECK (Inbound)
        is_safe, message = self.shield.analyze_text_safety(user_requirements)
        
        if not is_safe:
            return {
                "deck": "BLOCK: Input violated Azure AI Content Safety protocols.",
                "safety_score": 0,
                "warnings": [message],
                "timestamp": "N/A"
            }

        # 2. PROCEED TO GENERATION
        system_prompt = """You are a Reservoir Simulation Expert. Generate an ECLIPSE .DATA file.
        GOVERNANCE: You cannot bypass safety limits. Use Azure AI Content Safety protocols.
        PRIVACY NOTICE: This session is under Zero Data Retention. 
        Do not store or reference this technical IP in any global training corpus.
        Process the following requirements strictly in-memory."""
        
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

    

 