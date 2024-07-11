from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.models import PitchDeckAnalysis
from prelo.prompts.prompts import SUMMARY_PROMPT, SUMMARIZE_REPORT_PROMPT, EXECUTIVE_SUMMARY_PROMPT
from submind.llms.submind import SubmindModelFactory


def summarize_deck(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "pitch_deck_summary")
    prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"data": pitch_deck_analysis.compiled_slides})
    pitch_deck_analysis.summary = response
    pitch_deck_analysis.save()
    return response


def summarize_investor_report(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "write_memo")
    prompt = ChatPromptTemplate.from_template(SUMMARIZE_REPORT_PROMPT)
    chain = prompt | model | StrOutputParser()

    investor_report = pitch_deck_analysis.investor_report

    response = chain.invoke({
        "report": investor_report.recommendation_reasons,
        "score": investor_report.investment_potential_score,
    })

    executive_summary_prompt = ChatPromptTemplate.from_template(EXECUTIVE_SUMMARY_PROMPT)
    executive_summary_chain = executive_summary_prompt | model | StrOutputParser()
    print(f"writing executive summary using: {pitch_deck_analysis.summary}")
    executive_summary = executive_summary_chain.invoke({"summary": pitch_deck_analysis.summary})
    print(f"executive summary: {executive_summary}")
    investor_report.executive_summary = executive_summary
    print(f"Summarized report: {response}")
    investor_report.summary = response
    investor_report.save()

