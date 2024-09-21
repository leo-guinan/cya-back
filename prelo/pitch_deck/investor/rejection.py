from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.models import PitchDeckAnalysis, RejectionEmail, Investor
from prelo.prompts.functions import functions
from prelo.prompts.prompts import REJECTION_EMAIL_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind


def write_rejection_email(pitch_deck_analysis: PitchDeckAnalysis, investor: Investor, investor_submind: Submind):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "rejection_email")
    prompt = ChatPromptTemplate.from_template(REJECTION_EMAIL_PROMPT)
    chain = prompt | model.bind(function_call={"name": "rejection_email"},
                                functions=functions) | JsonOutputFunctionsParser()
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    submind_document = remember(submind)
    investor_document = remember(investor_submind)
    response = chain.invoke({
        "mind": submind_document,
        "report": pitch_deck_analysis.investor_report.recommendation_reasons,
        "score": pitch_deck_analysis.investor_report.investment_potential_score,
        "contact": pitch_deck_analysis.founder_contact_info,
        "investor_mind": investor_document

    })
    print(response)

    email = RejectionEmail.objects.create(deck_uuid=pitch_deck_analysis.deck.uuid,
                                          investor=investor,
                                          content=response['results']['body'],
                                          subject=response['results']['subject'],
                                          email=response['results']['email'],
                                          )


    return email, "email"