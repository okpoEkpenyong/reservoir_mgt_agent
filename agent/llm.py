import os
import streamlit as st
from huggingface_hub import InferenceClient
from groq import Groq
from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMEngine:
    def __init__(self):
        # Env variables provide the bridge between Local and Azure
        
        self.model = {
            "GROQ": os.getenv("GROQ_MODEL"),
            "AZURE": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        }
        #self.api_key =  GROQ_API_KEY
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        
    def analyze_reservoir_task(self, model_id, system_prompt, user_content):
        #if not self.client:
        #   return "Error: Groq client not initialized. Check GROQ_API_KEY environment variable."
        
        # We now use the standard Chat format (System Prompt + User Prompt)
        messages = [

            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

                
        if model_id == "AZURE":
            with st.spinner(f"Querying {self.model["AZURE"]} via AzureOpenAI Inference API..."):
                try:
                    
                    self.client = AzureOpenAI(
                        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_URL"),
                        api_key=os.getenv("AZURE_OPENAI_KEY"),
                        api_version=os.getenv("AZURE_OPENAI_VERSION"),
                    )

                    completion = self.client.chat.completions.create(
                        model=self.model["AZURE"],
                        messages=messages,
                    )


                    result_text = completion.choices[0].message.content
                    
                    st.success("Diagnostic Report Generated:")
                    st.info(f"**{self.model["AZURE"]} Output:**\n\n{result_text}")
                except Exception as e:
                    st.error(f"API Error: {e}. (Ensure your token has 'read' permissions and the model is loaded).")

        elif model_id == "GROQ":
            with st.spinner(f"Querying {self.model["GROQ"]} via GROQ Inference API..."):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model["GROQ"],
                        messages=messages,
                        #model="groq/compound",
                        temperature=1,
                        max_completion_tokens=7000,
                        top_p=1,
                        reasoning_effort="medium",
                        stream=True,
                        stop=None
                    )
                    
                    st.success("Diagnostic Report Generated:")

                   # Collection loop for streaming chunks
                    full_response = ""
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                        
                    st.info(f"**{self.model["GROQ"]} Output:**\n\n{full_response}")
                    
                except Exception as e:
                    st.error(f"API Error: {e}. (Ensure your token has 'read' permissions and the model is loaded).")

        else:
            # if no model is selected
            st.info("Select a model and click the button to generate the report.")    

    def ask(self, prompt: str, context: str = ""):
        """Standard wrapper for simpler queries."""
        return self.analyze_reservoir_task(
            model_id=self.model,
            system_prompt="You are a Senior Reservoir Engineer.",
            user_content=f"Context: {context}\n\nQuestion: {prompt}"
        )