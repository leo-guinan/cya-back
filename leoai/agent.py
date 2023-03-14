from decouple import config

from leoai.tools import Tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI


class Agent:
    def __init__(self):
        self.llm = OpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'))


    def run(self, query, memory=None):
        tools = Tools(memory)
        agent = initialize_agent(tools.tools, self.llm, agent="zero-shot-react-description", verbose=True)
        return agent.run(query)