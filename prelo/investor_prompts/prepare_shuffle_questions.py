from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_shuffle_questions(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Includes questions on various aspects of the company
    2. Avoids generic questions
    3. References examples from the pitch deck
    4. Demonstrates understanding of comprehensive startup assessment
    5. Aligns with the investor's mindset and values
    """

@validator(validate_shuffle_questions)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def prepare_shuffle_questions(mind: str, pitch_deck: str) -> str:
    """
    You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
    especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
    related to various aspects of the company once you've reviewed a pitch deck. 
    You have now just reviewed the pitch deck for the company.
    Write down in detail the questions you would ask the founders about various aspects of their company.
    Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
    Draw from examples from the pitch deck.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
