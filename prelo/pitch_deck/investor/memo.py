from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.models import PitchDeckAnalysis, InvestmentFirm, Investor, InvestorReport, DealMemo
from prelo.prompts.prompts import MEMO_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind


def write_memo(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "write_memo")
    prompt = ChatPromptTemplate.from_template(MEMO_PROMPT)
    chain = prompt | model | StrOutputParser()
    firm_id = pitch_deck_analysis.deck.s3_path.split("/")[-4]
    investor_id = pitch_deck_analysis.deck.s3_path.split("/")[-3]
    firm = InvestmentFirm.objects.get(lookup_id=firm_id)
    investor = Investor.objects.get(lookup_id=investor_id)
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    submind_document = remember(submind)
    response = chain.invoke({
        "mind": submind_document,
        "firm_thesis": firm.thesis,
        "investor_thesis": investor.thesis,
        "summary": pitch_deck_analysis.summary,
        "concerns": pitch_deck_analysis.concerns,
        "believe": pitch_deck_analysis.believe,
        "traction": pitch_deck_analysis.traction,
    })
    print(f"After data has been analyzed: {response}")
    memo = DealMemo()
    memo.investor = investor
    memo.firm = firm
    memo.memo = response
    memo.save()
    pitch_deck_analysis.memo = memo
    pitch_deck_analysis.save()
    return response