from decouple import config
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser, JsonKeyOutputFunctionsParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

functions = [
    {
        "name": "classify",
        "description": "A classification for a statement",
        "parameters": {
            "type": "object",
            "properties": {
                "classification": {"type": "string", "description": "The classification of the command"},
            },
            "required": ["classification"],
        },
    }
]


def classify_command(command):
    template = """
    You are a message classifier. 
    Determine whether the following message is a statement, a question, or a command.
    Respond in JSON format like this:
    {{
        "classification": "statement"
    }}
    
    Here's the message: {input}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4-turbo")
    chain = prompt | model.bind(function_call={"name": "classify"}, functions=functions) | JsonKeyOutputFunctionsParser(
        key_name="classification")
    response = chain.invoke({"input": command})
    print(response)
    return response
