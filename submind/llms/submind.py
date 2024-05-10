import threading

from decouple import config
from langchain_openai import ChatOpenAI


class SubmindModelFactory:

    @classmethod
    def get_model(cls, request_uuid, step, temperature=0.5):
        return ChatOpenAI(
            model="gpt-4-turbo",
            temperature=temperature,
            openai_api_key=config("OPENAI_API_KEY"),
            model_kwargs={
                "extra_headers": {
                    "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                    "Helicone-Property-UUID": request_uuid,
                    "Helicone-Property-Step": step

                }
            },
            openai_api_base="https://oai.hconeai.com/v1",
        )