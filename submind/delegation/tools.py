from decouple import config
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prelo.tools.company import query_records
from submind.functions.functions import functions
from submind.memory.memory import remember
from submind.models import Goal
from submind.prompts.prompts import TOOLS_PROMPT

AVAILABLE_TOOLS = [
    {
        "name": "Prelo",
        "description": "This tool allows you to get information about startups, their founders, and their fundraising efforts",
        "function": query_records
    }
]


def determine_tools(goal: Goal):
    mind = remember(goal.submind, goal.client.id)
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(TOOLS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "determine_tools_to_run"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="tools_needed")

    tools_to_run = []
    for tool in AVAILABLE_TOOLS:
        tools_to_run.append(
            f"Tool -- Name: {tool['name']} -- Description: {tool['description']}")

    response = chain.invoke(
        {"description": goal.submind.description, "tools": "\n".join(tools_to_run), "goal": goal.content, "mind": mind})

    print(response)

    return response


def run_tools(tools):
    # tools are context independent ways to fetch data for subminds to process
    compiled_results = []
    for tool in tools:
        runnable_tool = next((t for t in AVAILABLE_TOOLS if t["name"] == tool['tool_name']), None)
        if runnable_tool:
            result = runnable_tool["function"](tool['query'])
        else:
            print(f"Tool {tool} not found in available tools")
            result = None
        compiled_results.append(result)
    return "\n".join(compiled_results)
