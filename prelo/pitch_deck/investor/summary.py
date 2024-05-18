from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.models import PitchDeckAnalysis
from prelo.prompts.prompts import SUMMARY_PROMPT
from submind.llms.submind import SubmindModelFactory


def summarize_deck(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "pitch_deck_summary")
    prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"data": pitch_deck_analysis.compiled_slides})
    pitch_deck_analysis.summary = response
    pitch_deck_analysis.save()
    return response
