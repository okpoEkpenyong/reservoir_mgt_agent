import os
from openai import OpenAI

class LLMEngine:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "GROQ").upper()
        
        if self.provider == "OPENAI":
            # Groq is OpenAI-compatible but much faster
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY")
            )
            self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            
        elif self.provider == "QWEN":
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY")
            )
            self.model = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")

    def ask(self, prompt: str, context: str = ""):
        if not self.client.api_key:
            return f"Error: {self.provider}_API_KEY is missing from Key Vault."
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Senior Reservoir Simulation Expert. Use professional technical language."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{prompt}"}
                ],
                temperature=1,
                max_completion_tokens=8192,
                top_p=1,
                reasoning_effort="medium",
                stream=True,
                stop=None
            )
            #return response.choices[0].message.content
            return response.choices[0].delta.content
        except Exception as e:
            return f"{self.provider} Error: {str(e)}"
