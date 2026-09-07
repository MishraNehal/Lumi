# import os
# from huggingface_hub import InferenceClient


# MODEL_NAME = "HuggingFaceH4/zephyr-7b-beta"


# class HuggingFaceLLM:
#     def __init__(self):
#         self.client = InferenceClient(
#             model=MODEL_NAME,
#             token=os.getenv("HF_API_TOKEN")
#         )

#     def generate(self, prompt: str) -> str:
#         response = self.client.chat_completion(
#             messages=[
#                 {"role": "system", "content": "You are Lumi, a helpful AI assistant."},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=512,
#             temperature=0.2,
#         )

#         return response.choices[0].message.content.strip()


# hf_llm = HuggingFaceLLM()

import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# ─────────────────────────────────────────
# LOAD .env WITH EXPLICIT PATH
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)


class GroqLLM:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Add it to your .env file.")
        self.model_name = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-20b")
        self.client = Groq(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are Lumi, an intelligent AI knowledge assistant. "
                            "You answer questions strictly based on provided context. "
                            "Be concise, accurate, and cite sources when possible."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=512,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"


# Single shared instance — same variable name so rag_chain.py needs no changes
hf_llm = GroqLLM()