from decouple import config
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser, JsonKeyOutputFunctionsParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

functions = [
    {
        "name": "schema_to_body",
        "description": "Transform a schema to a body",
        "parameters": {
            "type": "object",
            "properties": {
                "classification": {"type": "string", "description": "The classification of the command"},
            },
            "required": ["classification"],
        },
    }
]


def schema_to_body(command, input_schema):
    template = """
    You are a message transformer. Given a message that uses this input format:
    {input_schema}
    
    Transform it into a JSON object that can be passed as the body of an HTTP request.
     
    Respond with only the JSON object.

    Here's the message: {message}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4")
    chain = prompt | model
    response = chain.invoke({"message": command,"input_schema": input_schema})
    print(response)
    return response
