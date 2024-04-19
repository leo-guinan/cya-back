from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from submind.prompts.prompts import COMPLETE_RESEARCH_PROMPT


def compile_answers(thoughts, submind, mind, question):
    model = ChatOpenAI(model="gpt-4", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(COMPLETE_RESEARCH_PROMPT)
    output_parser = StrOutputParser()
    chain = prompt | model | output_parser

    combined = "Research Summary:\n\n"
    for thought in thoughts:
        combined += f"{thought.question.content}:\n{thought.content}\n\n"

    response = chain.invoke(
        {"description": submind.description,
         "mind": mind,
         "question": question,
         "research": combined})
    print(response)
    return response
