from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from submind.memory.memory import remember
from submind.models import Goal
from submind.prompts.prompts import REMEMBER_PROMPT


def answer_from_memory(goal: Goal):
    mind = remember(goal.submind, goal.client.id if goal.client else None)
    model = ChatOpenAI(model="gpt-4", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(REMEMBER_PROMPT)
    output_parser = StrOutputParser()
    chain = prompt | model | output_parser
    response = chain.invoke({"description": goal.submind.description, "mind": mind, "question": goal.content})
    goal.results = response
    goal.completed = True
    goal.save()
    return response