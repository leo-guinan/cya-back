from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from submind.llms.submind import SubmindModelFactory
from submind.prompts.prompts import COMPLETE_RESEARCH_PROMPT


def compile_thought_answers(thoughts, submind, mind, question):
    print("Compiling thought answers")
    model = SubmindModelFactory.get_model(submind.uuid, "compile_thought_answers")
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
    return response


def compile_goal_answers(responses, submind, mind, question):
    print("Compiling goal answers")
    model = SubmindModelFactory.get_model(submind.uuid, "compile_goal_answers")
    prompt = ChatPromptTemplate.from_template(COMPLETE_RESEARCH_PROMPT)
    output_parser = StrOutputParser()
    chain = prompt | model | output_parser

    combined = "Research Summary:\n\n"
    for response in responses:
        combined += f"{response['question']}:\n{response['answer']}\n\n"

    response = chain.invoke(
        {"description": submind.description,
         "mind": mind,
         "question": question,
         "research": combined})
    return response
