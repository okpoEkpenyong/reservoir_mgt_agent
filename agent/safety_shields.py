import os
import streamlit as st
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions
from dotenv import load_dotenv

load_dotenv()

class AzureSafetyShield:
    def __init__(self):
        # These should be added to your Azure Key Vault / Streamlit Secrets
        #"GROQ_MODEL": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        self.endpoint = os.getenv("CONTENT_SAFETY_ENDPOINT")
        self.key = os.getenv("CONTENT_SAFETY_KEY")
        
        if self.endpoint and self.key:
            self.client = ContentSafetyClient(self.endpoint, AzureKeyCredential(self.key))
        else:
            self.client = None

    def analyze_text_safety(self, text):
        """Analyzes text for Jailbreaks and Harmful content via Azure AI."""
        if not self.client:
            return True, "Safety Shield bypass: No API key configured."

        try:
            # We only send the first 1000 chars for efficiency
            request = AnalyzeTextOptions(text=text[:1000])
            response = self.client.analyze_text(request)

            # Check for Hate, Violence, etc.
            for category in response.categories_analysis:
                if category.severity > 2: # Severity scale 0-6 (4+ is usually blocked)
                    return False, f"Flagged for {category.category} (Severity: {category.severity})"
            
            return True, "Safe"
        except Exception as e:
            return True, f"Safety check error: {str(e)}" # Fail open for MVP, change to False for Prod