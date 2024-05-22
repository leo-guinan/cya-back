import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.investor.prompts.llm import functions
from prelo.models import PitchDeckAnalysis
from prelo.prompts.prompts import CONCERNS_PROMPT
from submind.llms.submind import SubmindModelFactory


def concerns_analysis(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "concerns")
    prompt = ChatPromptTemplate.from_template(CONCERNS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "concerns_analysis"},
                                functions=functions) | JsonOutputFunctionsParser()
    response = chain.invoke({"data": pitch_deck_analysis.compiled_slides})
    pitch_deck_analysis.concerns = json.dumps(response)
    pitch_deck_analysis.save()
    return response
