from decouple import config
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from submind.functions.functions import functions
from submind.memory.memory import remember
from submind.models import Goal
from submind.prompts.prompts import DELEGATION_PROMPT


def delegate(goal: Goal, tool_info: str):
    mind = remember(goal.submind, goal.client.id)
    model = ChatOpenAI(model="gpt-4", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(DELEGATION_PROMPT)
    chain = prompt | model.bind(function_call={"name": "delegate_to_subminds"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="delegated_questions")

    prepped_subminds = []
    for submind in goal.submind.subminds.all():
        prepped_subminds.append(
            f"Submind -- Id: {submind.id} -- Name: {submind.name} -- Description: {submind.description}")

    response = chain.invoke(
        {"description": goal.submind.description,
         "subminds": prepped_subminds,
         "goal": goal.content,
         "mind": mind,
         "data": tool_info})

    print(response)

    return response
