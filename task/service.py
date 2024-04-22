from decouple import config
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
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
    },
    {
        "name": "generate_tasks",
        "description": "A generator of tasks based on a plan",
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "The tasks contained in the plan",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "The name of the task"},
                            "details": {"type": "string", "description": "The details of the task"},
                            "dependsOn": {"type": "array", "description": "The tasks the task depends on",
                                          "items": {
                                              "type": "string",
                                              "description": "The name of the task the task depends on"
                                          }
                                          },
                            "subtasks": {
                                "type": "array",
                                "description": "The subtasks of the task",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "The name of the subtask"
                                        },
                                        "details": {
                                            "type": "string",
                                            "description": "The details of the subtask"
                                        },
                                        "dependsOn": {
                                            "type": "array",
                                            "description": "The tasks the subtask depends on",
                                            "items": {
                                                "type": "string",
                                                "description": "The name of the task the task depends on"

                                            }
                                        }
                                    }
                                }
                            }
                        },
                    },
                    "required": ["tasks"],
                },
            }
        }
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
    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4-turbo")
    chain = prompt | model.bind(function_call={"name": "identify_tasks"},
                                functions=functions) | JsonKeyOutputFunctionsParser(
        key_name="tasks")
    response = chain.invoke({"input": command})
    return response


def generateTasksFromPlan(plan):
    template = """
        You are an expert in task identification and relations.
        
        Your job is to identify the tasks and their subtasks from the plan, and the dependencies between them. 
        You should return the tasks and their subtasks in the following JSON format:
        {{
            "tasks": [
                {{
                    "name": "<short name of the task>",
                    "details": "<details of the task>",
                    "dependsOn": ["<short name of the task>", "<short name of the task>"],
                    "subtasks": [
                        {{
                            "name": "<short name of the subtask>",
                            "details": "<details of the subtask>"
                            "dependsOn": ["<short name of the subtask>", "<short name of the subtask>"],
                        }}
                    ]
                }}
            ]
        }}

        Here's the message: {input}
        """
    prompt = ChatPromptTemplate.from_template(template=template)
    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4-turbo")
    chain = prompt | model.bind(function_call={"name": "generate_tasks"},
                                functions=functions) | JsonKeyOutputFunctionsParser(
        key_name="tasks")
    response = chain.invoke({"input": plan})
    print("task plan tasks", response)
    return response
