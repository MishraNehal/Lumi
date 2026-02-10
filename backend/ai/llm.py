import os
from huggingface_hub import InferenceClient


MODEL_NAME = "HuggingFaceH4/zephyr-7b-beta"


class HuggingFaceLLM:
    def __init__(self):
        self.client = InferenceClient(
            model=MODEL_NAME,
            token=os.getenv("HF_API_TOKEN")
        )

    def generate(self, prompt: str) -> str:
        response = self.client.chat_completion(
            messages=[
                {"role": "system", "content": "You are Lumi, a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.2,
        )

        return response.choices[0].message.content.strip()


hf_llm = HuggingFaceLLM()
