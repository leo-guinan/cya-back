from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_founder_domain_experience(mind: str, pitch_deck: str, social_media: str) -> str:
    return """
    Evaluate if the output:
    1. Articulates each founder's domain expertise clearly
    2. Explains how the expertise translates to building a successful startup
    3. Includes relevant social media links
    4. Uses a table format with appropriate headers and structure
    5. Provides specific, non-generic information based on the pitch deck
    """

@validator(validate_founder_domain_experience)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def research_founders_founder_domain_experience(mind: str, pitch_deck: str, social_media: str) -> str:
    """
    You've done some early investigation on the founders of the company, 
    you've also read the pitch deck and deeply understand the founders' backgrounds. 
    Articulate very succinctly each founder's domain expertise and how it translates 
    to being useful for building a successful Startup in beehiiv. Include social media links.
    Create a table with the founder names as the headers and the 3 main rows as the founder expertise
    and social media links as the others.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}\nHere are the known social media links for the founders:\n{social_media}"
