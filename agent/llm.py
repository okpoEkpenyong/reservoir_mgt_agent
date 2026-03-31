import os
from huggingface_hub import InferenceClient

class LLMEngine:
    def __init__(self):
        # Retrieve the token
        token = os.getenv("HF_TOKEN")
        
        # Validation: Check if Key Vault failed to provide the real secret
        if not token:
            self.client = None
            self.error = "HF_TOKEN environment variable is missing."
        elif token.startswith("@Microsoft.KeyVault"):
            self.client = None
            self.error = "Key Vault Reference not resolved. Azure is still authenticating. Please wait 60s and refresh."
        else:
            self.client = InferenceClient(token=token)
            self.error = None

    def analyze_reservoir_task(self, model_id, system_prompt, user_content):
        if self.error:
            return self.error
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        try:
            # We pass the model explicitly to avoid the auto-router error
            response = self.client.chat_completion(
                model=model_id,
                messages=messages,
                max_tokens=5000,
                
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Hugging Face Error: {str(e)}"
