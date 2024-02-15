from decouple import config
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser, JsonKeyOutputFunctionsParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

functions = [
    {
        "name": "identify_tasks",
        "description": "An identifier of tasks",
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "The tasks contained in the message",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "The name of the task"},
                            "details": {"type": "string", "description": "The details of the task"},
                            "taskFor": {"type": "string", "description": "The person the task is for"}
                        }
                    }
                },
            },
            "required": ["tasks"],
        },
    }
]


def identify_tasks(command):
    template = """
    You are a task identifier. 
    If the following message has contains any tasks to do, identify them and return them in the this JSON format:
    {{
        "tasks": [
            {{
                "name": "<short name of the task>",
                "details": "<details of the task>",
                "taskFor": "<who the task is for>"
            }}
        ]
    }}

    Here's the message: {input}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4")
    chain = prompt | model.bind(function_call={"name": "identify_tasks"}, functions=functions) | JsonKeyOutputFunctionsParser(
        key_name="tasks")
    response = chain.invoke({"input": command})
    return response
