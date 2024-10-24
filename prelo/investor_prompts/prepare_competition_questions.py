from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_competition_questions(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Focuses specifically on questions related to competition
    2. Avoids generic questions
    3. References examples from the pitch deck
    4. Demonstrates understanding of competitive landscape assessment for early-stage startups
    5. Aligns with the investor's mindset and values
    """

@validator(validate_competition_questions)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def prepare_competition_questions(mind: str, pitch_deck: str) -> str:
    """
    You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
    especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
    related to competition once you've reviewed a pitch deck. 
    You have now just reviewed the Competitors slides for the company.
    Write down in detail the questions you would ask the founders about their competition.
    Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
    Draw from examples from the pitch deck.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
