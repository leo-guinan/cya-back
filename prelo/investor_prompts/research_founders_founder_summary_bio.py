from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_founder_summary_bio(mind: str, pitch_deck: str, social_media: str) -> str:
    return """
    Evaluate if the output:
    1. Provides a concise summary bio for each founder
    2. Articulates how each founder's experience translates to startup success
    3. Includes relevant social media information
    4. Demonstrates understanding of founder assessment for startups
    5. Provides specific, non-generic information based on the pitch deck
    """

@validator(validate_founder_summary_bio)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def research_founders_founder_summary_bio(mind: str, pitch_deck: str, social_media: str) -> str:
    """
    You've done some early investigation on the founders of the company,
    you've also read the pitch deck and deeply understand the founders' backgrounds. 
    Share a short summary bio of each of the founders and articulate specifically how their 
    experiences will directly translate to the success of their startup.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}\nHere are the known social media links for the founders:\n{social_media}"
