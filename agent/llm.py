import os
from openai import OpenAI, AzureOpenAI

class LLMEngine:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "HUGGINGFACE").upper()
        
        if self.provider == "HUGGINGFACE":
            # Hugging Face Inference API is OpenAI-compatible
            self.client = OpenAI(
                base_url="https://api-inference.huggingface.co/v1",
                api_key=os.getenv("HF_TOKEN")
            )
            self.model = os.getenv("HF_MODEL_ID", "Qwen/Qwen3.5-397B-A17B")
            
        elif self.provider == "AZURE_OPENAI":
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-02-01",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            self.model = os.getenv("AZURE_OPENAI_MODEL", "gpt-5.4")

    def ask(self, prompt: str, context: str = ""):
        try:
            msg = f"Context:\n{context}\n\nQuestion:\n{prompt}"
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Reservoir Engineering Expert. Use SI units unless asked otherwise."},
                    {"role": "user", "content": msg}
                ],
                temperature=0.1,
                max_tokens=3800
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error using {self.provider}: {str(e)}"
