from decouple import config
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from submind.functions.functions import functions
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Goal, Submind
from submind.prompts.prompts import DELEGATION_PROMPT, SPAWN_SUBMINDS_PROMPT, ANSWER_PROMPT


def delegate(goal: Goal, tool_info: str, shallow: bool = True):
    mind = remember(goal.submind)
    model = SubmindModelFactory.get_model(goal.submind.uuid, "delegate")
    if shallow:
        prompt = ChatPromptTemplate.from_template(ANSWER_PROMPT)
        chain = prompt | model.bind(function_call={"name": "answer_and_skip_delegation"},
                                    functions=functions) | JsonOutputFunctionsParser()

        response = chain.invoke(
            {"description": goal.submind.description,
             "goal": goal.content,
             "mind": mind,
             "data": tool_info})
    else:
        prompt = ChatPromptTemplate.from_template(DELEGATION_PROMPT)
        chain = prompt | model.bind(function_call={"name": "delegate_to_subminds"},
                                    functions=functions) | JsonOutputFunctionsParser()
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


def spawn_children(goal: Goal, parent_submind: Submind):
    mind = remember(parent_submind)
    model = SubmindModelFactory.get_model(goal.submind.uuid, "spawn_children")
    prompt = ChatPromptTemplate.from_template(SPAWN_SUBMINDS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "spawn_subminds"},
                                functions=functions) | JsonOutputFunctionsParser()

    response = chain.invoke(
        {"description": goal.submind.description,
         "goal": goal.content,
         "mind": mind,
         })

    print(response)

    return response['subminds']
