from .llm import LLMEngine

import pandas as pd
import numpy as np
import io

class ReservoirAgent:
    def __init__(self):
        self.engine = LLMEngine()

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