import re
import uuid

from decouple import config
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from podcast.models import PodcastQuery
from podcast.tasks import search
from submind.functions.functions import functions
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Question, Thought
from submind.prompts.prompts import ANSWER_TEMPLATE, RESEARCH_PROMPT, HUMAN_MESSAGE_TEMPLATE
from submind.tools.answers import compile_thought_answers


def research(goal):
    print("Attempting to research")
    mind = remember(goal.submind)
    model = SubmindModelFactory.get_model(goal.submind.uuid, "research")
    prompt = ChatPromptTemplate.from_template(RESEARCH_PROMPT)
    chain = prompt | model.bind(function_call={"name": "research_questions"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="research")
    response = chain.invoke({"description": goal.submind.description, "mind": mind, "question": goal.content})
    thoughts = []
    for question in response['research_questions']:
        answer = answer_question(question, goal.submind.uuid)
        new_question = Question.objects.create(content=question, goal_id=goal.id, uuid=str(uuid.uuid4()),
                                               submind_id=goal.submind.id)
        thought = Thought.objects.create(content=answer, submind_id=goal.submind.id, uuid=str(uuid.uuid4()),
                                         question_id=new_question.id)

        thoughts.append(thought)

    final_answer = compile_thought_answers(thoughts, goal.submind, mind, goal.content)
    goal.results = final_answer
    goal.completed = True
    goal.save()
    return final_answer


def answer_question(question, goal_uuid):
    print("Attempting to answer question")
    podcast_query = PodcastQuery.objects.create(query=question)

    search(podcast_query.id)

    snippets = podcast_query.snippets.all()

    return compile_snippets_into_answer(snippets, question, goal_uuid)


def compile_snippets_into_answer(snippets, question, goal_uuid):
    model_35 = ChatOpenAI(
        model="gpt-3.5-turbo",
        openai_api_key=config("OPENAI_API_KEY"),
        model_kwargs={
            "extra_headers": {
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                "Helicone-Property-UUID": goal_uuid,
                "Helicone-Property-Step": "snippets_to_answer"

            }
        },
        openai_api_base="https://oai.hconeai.com/v1",
    )
    model_4 = ChatOpenAI(
        model="gpt-4-turbo",
        openai_api_key=config("OPENAI_API_KEY"),
        model_kwargs={
            "extra_headers": {
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                "Helicone-Property-UUID": goal_uuid,
                "Helicone-Property-Step": "snippets_to_answer"

            }
        },
        openai_api_base="https://oai.hconeai.com/v1",
    )
    model_claude = ChatAnthropic(model_name="claude-3-haiku-20240307",
                                 anthropic_api_key=config("ANTHROPIC_API_KEY"),
                                 anthropic_api_url="https://anthropic.hconeai.com/",
                                 model_kwargs={
                                     "extra_headers": {
                                         "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                                         "Helicone-Property-Step": "snippets_to_answer",
                                         "Helicone-Property-UUID": goal_uuid,

                                     }
                                 }
                                 )
    prompt = ChatPromptTemplate.from_messages([("system", ANSWER_TEMPLATE), ("human", HUMAN_MESSAGE_TEMPLATE)])
    output_parser = StrOutputParser()
    current_answer = ""
    for snippet in snippets:

        try:
            chain = prompt | model_claude | output_parser
            # remove all timestamps in [] brackets
            cleaned_text = re.sub(r'\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]', '',
                                  snippet.snippet)
            current_answer = chain.invoke(
                {"question": question,
                 "answer": current_answer,
                 "snippet": cleaned_text
                 })
        except Exception as e:
            try:
                print("Failed to get answer from claude-3-haiku-20240307, using gpt-3.5-turbo")
                print(e)
                chain = prompt | model_35 | output_parser
                # remove all timestamps in [] brackets
                cleaned_text = re.sub(r'\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]', '',
                                      snippet.snippet)

                current_answer = chain.invoke(
                    {"question": question,
                     "answer": current_answer,
                     "snippet": cleaned_text
                     })
            except Exception as e2:
                try:
                    print("Failed to get answer from gpt-3.5-turbo, using gpt-4-turbo")
                    print(e2)
                    chain = prompt | model_4 | output_parser
                    # remove all timestamps in [] brackets
                    cleaned_text = re.sub(r'\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]', '',
                                          snippet.snippet)

                    current_answer = chain.invoke(
                        {"question": question,
                         "answer": current_answer,
                         "snippet": cleaned_text
                         })

                except Exception as e3:
                    print("Failed to get answer")
                    print(e3)
                    continue
    return current_answer
