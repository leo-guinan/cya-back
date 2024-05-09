from decouple import config
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prelo.tools.company import query_records
from prelo.tools.deck import answer_question_about_deck, answer_question_about_slide, answer_question_about_company, \
    answer_question_about_founder
from submind.functions.functions import functions
from submind.memory.memory import remember
from submind.models import Goal
from submind.prompts.prompts import TOOLS_PROMPT

AVAILABLE_TOOLS = [
    {
        "name": "Prelo",
        "description": "This tool allows you to get information about startups, their founders, and their fundraising efforts",
        "function": query_records
    },
{
        "name": "Pitch Deck Info",
        "description": "This tool allows you to get information about a specific pitch deck. It requires the inquiry and the uuid of the deck to lookup.",
        "function": answer_question_about_deck
    },
{
        "name": "Pitch Deck Slide Info",
        "description": "This tool allows you to get information about a specific slide in a pitch deck. It requires the inquiry, the uuid of the deck to lookup, and the slide numbers that you want to look up.",
        "function": answer_question_about_slide
    },
{
        "name": "Pitch Deck Company Info",
        "description": "This tool allows you to get information about the company in a pitch deck",
        "function": answer_question_about_company
    },
{
        "name": "Pitch Deck Founder Info",
        "description": "This tool allows you to get information about the founder(s) in a pitch deck",
        "function": answer_question_about_founder
    }
]


def determine_tools(goal: Goal):
    mind = remember(goal.submind)
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
    compiled_results = ""
    for tool in tools:
        runnable_tool = next((t for t in AVAILABLE_TOOLS if t["name"] == tool['tool_name']), None)
        if runnable_tool:
            result = runnable_tool["function"](tool['query'], tool['data_to_send'], compiled_results)
        else:
            print(f"Tool {tool} not found in available tools")
            result = None
        compiled_results += f"{tool['query']}\n{result}"
    return compiled_results
