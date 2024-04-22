from decouple import config
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser, JsonKeyOutputFunctionsParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def schema_to_body(command, input_schema, session_id):
    template = f"""
    You are a message transformer. Given a message that uses this input format:
    {input_schema}
    
    Here's the session_id for the user: {session_id}
    
    Transform it into a JSON object that can be passed as the body of an HTTP request.
     
    Respond with only the JSON object.

    Here's the message: {command}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4-turbo")
    chain = prompt | model
    response = chain.invoke({"message": command,"input_schema": input_schema, "session_id":session_id})
    print(response)
    return response.content
