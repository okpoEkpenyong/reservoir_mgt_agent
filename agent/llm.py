import os
from huggingface_hub import InferenceClient

class LLMEngine:
    def __init__(self):
        # Tokens are pulled from Key Vault via App Settings
        self.token = os.getenv("HF_TOKEN")
        self.default_model = os.getenv("HF_MODEL_ID", "Qwen/Qwen3.5-397B-A17B")
        
        if self.token:
            self.client = InferenceClient(token=self.token)
        else:
            self.client = None

    def analyze_reservoir_task(self, model_id, system_prompt, user_content):
        if not self.client:
            return "Error: No Hugging Face Token found. Check Azure Key Vault."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        try:
            response = self.client.chat_completion(
                model=model_id or self.default_model,
                messages=messages,
                max_tokens=3000,
                temperature=0.9 # Low temperature for technical precision
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Inference Error: {str(e)}"
