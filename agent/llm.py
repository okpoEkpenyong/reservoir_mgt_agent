from openai import AzureOpenAI

class LLMEngine:
    """
    Wrapper around Azure OpenAI to make calls stable and safe.
    """

    def __init__(self, api_key, endpoint, deployment):
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-02-01"
        )
        self.deployment = deployment

    def ask(self, prompt: str, context: str = ""):
        """Send a structured prompt to Azure OpenAI."""
        msg = f"Context:\n{context}\n\nQuestion:\n{prompt}"

        completion = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": msg}],
            max_tokens=400,
            temperature=0.0
        )
        return completion.choices[0].message.content
