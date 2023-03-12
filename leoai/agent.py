from decouple import config

from leoai.tools import Tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI


class Agent:
    def __init__(self):
        llm = OpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'))
        tools = Tools()
        self.agent = initialize_agent(tools.tools, llm, agent="zero-shot-react-description", verbose=True)

    def run(self, query):
        return self.agent.run(query)