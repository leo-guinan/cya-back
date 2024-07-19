import threading

from decouple import config
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama


class SubmindModelFactory:

    @classmethod
    def get_model(cls, request_uuid, step, temperature=0.5):
        return ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            openai_api_key=config("OPENAI_API_KEY"),
            model_kwargs={
                "extra_headers": {
                    "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                    "Helicone-Property-UUID": request_uuid,
                    "Helicone-Property-Step": step,
                    "Helicone-Property-Environment": "production",

                }
            },
            openai_api_base="https://oai.hconeai.com/v1",
        )

    @classmethod
    def get_mini(cls, request_uuid, step, temperature=0.5):
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            openai_api_key=config("OPENAI_API_KEY"),
            model_kwargs={
                "extra_headers": {
                    "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                    "Helicone-Property-UUID": request_uuid,
                    "Helicone-Property-Step": step,
                    "Helicone-Property-Environment": "production",

                }
            },
            openai_api_base="https://oai.hconeai.com/v1",
        )

    @classmethod
    def get_claude(cls, request_uuid, step):
        return ChatAnthropic(model_name="claude-3-5-sonnet-20240620",
                                 anthropic_api_key=config("ANTHROPIC_API_KEY"),
                                 anthropic_api_url="https://anthropic.hconeai.com/",
                                 max_tokens=4096,
                                 model_kwargs={
                                     "extra_headers": {
                                         "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                                         "Helicone-Property-Step": step,
                                         "Helicone-Property-UUID": request_uuid,

                                     }
                                 }
                                 )

    @classmethod
    def get_ollama(cls, request_uuid, step):
        return Ollama(model="llama3")
