import os
import streamlit as st
from groq import Groq
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMEngine:
    def __init__(self):
        self.configs = {
            "GROQ_MODEL": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "AZURE_DEPLOYMENT": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-main"),
            "AZURE_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT_URL"),
            "AZURE_KEY": os.getenv("AZURE_OPENAI_KEY"),
            "AZURE_VERSION": os.getenv("AZURE_OPENAI_VERSION", "2025-01-01-preview"),
            "GROQ_KEY": os.getenv("GROQ_API_KEY")
        }

    def analyze_reservoir_task(self, provider, system_prompt, user_content):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        if provider == "AZURE":
            if not self.configs["AZURE_KEY"] or self.configs["AZURE_KEY"].startswith("@Microsoft"):
                return "Error: Azure OpenAI Key not resolved."

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

        elif provider == "GROQ":
            if not self.configs["GROQ_KEY"] or self.configs["GROQ_KEY"].startswith("@Microsoft"):
                return "Error: GROQ_API_KEY missing."

            try:
                client = Groq(api_key=self.configs["GROQ_KEY"])
                completion = client.chat.completions.create(
                    model=self.configs["GROQ_MODEL"],
                    messages=messages,
                    temperature=0.7,
                    stream=False # Set to False for easier UI handling in data analysis
                )
                return completion.choices[0].message.content         
            except Exception as e:
                if "rate_limit_exceeded" in str(e).lower():
                    return "ERROR: The requested model is currently at capacity. Please switch the 'Reasoning Engine' to AZURE in the sidebar and try again."
                return f"Technical Error: {str(e)}"            
        return "Invalid provider."