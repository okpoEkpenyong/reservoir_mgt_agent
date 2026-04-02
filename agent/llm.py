import os
import streamlit as st
from groq import Groq
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMEngine:
    def __init__(self):
        # Load configs into a dictionary for easy access
        self.configs = {
            "GROQ_MODEL": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "AZURE_DEPLOYMENT": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-main"),
            "AZURE_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT_URL"),
            "AZURE_KEY": os.getenv("AZURE_OPENAI_KEY"),
            "AZURE_VERSION": os.getenv("AZURE_OPENAI_VERSION", "2025-01-01-preview"),
            "GROQ_KEY": os.getenv("GROQ_API_KEY")
        }

    def analyze_reservoir_task(self, provider, system_prompt, user_content):
        """
        Unified method to handle the logic. 
        Provider should be "AZURE" or "GROQ".
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        # --- AZURE OPENAI LOGIC ---
        if provider == "AZURE":
            # Guard Clause for Azure
            if not self.configs["AZURE_KEY"] or self.configs["AZURE_KEY"].startswith("@Microsoft"):
                return "Error: Azure OpenAI Key not resolved. Check Key Vault."

            with st.spinner(f"Querying {self.configs['AZURE_DEPLOYMENT']}..."):
                try:
                    client = AzureOpenAI(
                        azure_endpoint=self.configs["AZURE_ENDPOINT"],
                        api_key=self.configs["AZURE_KEY"],
                        api_version=self.configs["AZURE_VERSION"],
                    )
                    completion = client.chat.completions.create(
                        model=self.configs["AZURE_DEPLOYMENT"],
                        messages=messages,
                    )
                    return completion.choices[0].message.content
                except Exception as e:
                    return f"Azure API Error: {str(e)}"

        # --- GROQ LOGIC ---
        elif provider == "GROQ":
            # Guard Clause for Groq
            if not self.configs["GROQ_KEY"] or self.configs["GROQ_KEY"].startswith("@Microsoft"):
                return "Error: GROQ_API_KEY missing or unresolved."

            with st.spinner(f"Querying {self.configs['GROQ_MODEL']}..."):
                try:
                    client = Groq(api_key=self.configs["GROQ_KEY"])
                    completion = client.chat.completions.create(
                        model=self.configs["GROQ_MODEL"],
                        messages=messages,
                        temperature=0.7, # Adjusted from 1 for better technical stability
                        max_completion_tokens=4096,
                        stream=True
                    )
                    
                    # Collection loop for streaming chunks
                    full_response = ""
                    # Create a placeholder in the UI for streaming
                    placeholder = st.empty()
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response)
                    
                    return full_response
                except Exception as e:
                    return f"Groq API Error: {str(e)}"

        return "Please select a valid provider (AZURE or GROQ)."

    def ask(self, prompt: str, context: str = ""):
        # Default to AZURE for the quick 'ask'
        return self.analyze_reservoir_task(
            provider="AZURE",
            system_prompt="You are a Senior Reservoir Engineer.",
            user_content=f"Context: {context}\n\nQuestion: {prompt}"
        )