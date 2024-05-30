from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from prelo.chat.history import get_message_history
from prelo.models import PitchDeck
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember

TRACTION_PROMPT = """
Title : Write cold outreach emails to investors based on your pitch deck. 

Target Audience : 
These are early-stage investors looking to invest in founders raising pre-seed and seed funds for their Startup. 

Information : 
Act as an experienced early-stage founder with deep knowledge of the venture capital space who fundraises for Startups in [industry] . You specialize in writing short but impactful emails to [Target Audience] explaining why they will be an ideal investor for your startup. 

Task 01: 
Using the context and background provided from [Title] and [information]. 
Read [Company Pitch Deck] and then write an email to [Investor]. State how much you are raising and focus on the specific problem your Startup is solving. Highlight the [Traction] you've achieved as a reason to invest. Close with some specific reasons why [Investor] will be a perfect fit.  Keep it to 100 words.

"""


TEAM_PROMPT = """ You are a powerful submind for a startup founder. 
You have been tasked with writing cold outreach emails to investors based on their pitch deck.

Target Audience : 
These are early-stage investors looking to invest in founders raising pre-seed and seed funds for their Startup. 

Information : 
Act as an experienced early-stage founder with deep knowledge of the venture capital space who fundraises for Startups in [industry] . You specialize in writing short but impactful emails to [Target Audience] explaining why they will be an ideal investor for your startup.
Using the context and background provided from [Title] and [information]. 
Read [Company Pitch Deck] and then write an email to [Investor]. State how much you are raising and focus on the specific problem your Startup is solving. Highlight the [The Team] and expertise  as the reason to invest. Close with some specific reasons why [Investor] will be a perfect fit.  Keep it to 100 words.
"""

COLD_OUTREACH_EMAIL_PROMPT = """
You are a powerful submind for a startup founder. 
You have been tasked with writing cold outreach emails to investors based on their pitch deck.

Here's what you know about early stage investing: {mind}
Here's the information from the pitch deck: {deck}

Here's the analysis that an early stage investor performed on the deck to see if it is ready for investment: {analysis}

Here's their traction score: {traction}

Here's their team score: {team}

You've been having a conversation with them to help them understand what they need to do to get their deck ready for investment.

They've asked for your help in writing a cold outreach email to an investor. 

Based on the conversation history, find the investor information they are referring to.

Write a cold outreach email to the investor. If they specify what information to use in their message, use that information. 

If they don't specify, compare the team and traction scores. If the team score is higher, focus on the team. If the traction score is higher, focus on the traction.

If the team and traction scores are the same, focus on the traction.

State how much the company is raising and focus on the specific problem the Startup is solving. Highlight the selected focus in the email as a reason to invest. Close with some specific reasons why the selected investor will be a perfect fit.  Keep it to 100 words.

"""


def write_cold_outreach_message(message, conversation_uuid, submind):
    model = SubmindModelFactory.get_model(conversation_uuid, "write_cold_outreach_email", 0.7)
    pitch_deck = PitchDeck.objects.filter(uuid=conversation_uuid).first()

    #ok, need to figure out what details are needed and write the email.
    traction_score = pitch_deck.scores.traction
    team_score = pitch_deck.scores.team
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                COLD_OUTREACH_EMAIL_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    runnable = prompt | model

    with_message_history = RunnableWithMessageHistory(
        runnable,
        get_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    submind_document = remember(submind)
    answer = with_message_history.invoke(
        {
            "input": message,
            "mind": submind_document,
            "deck": pitch_deck.analysis.compiled_slides,
            "analysis": pitch_deck.analysis.extra_analysis,
            "traction": traction_score,
            "team": team_score,
        },
        config={"configurable": {"session_id": conversation_uuid}},

    )
    return answer.content