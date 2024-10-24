from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_founder_rating(mind: str, pitch_deck: str, social_media: str) -> str:
    return """
    Evaluate if the output:
    1. Provides a clear percentage rating for each founder
    2. Explains the rationale behind each rating
    3. Includes relevant social media links
    4. Uses a table format with appropriate headers and structure
    5. Demonstrates understanding of founder assessment for startups
    """

@validator(validate_founder_rating)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def research_founders_why_we_rate_the_founder(mind: str, pitch_deck: str, social_media: str) -> str:
    """
    You are an experienced startup researcher with 10 years experience of analyzing startup teams 
    and how their experience impacts the success of a startup. 
    Can you share each founder's percentage rating to indicate their importance to the Startup? 
    Include their social media links. 
    Create a table with the founder names as the headers and the 2 main rows as the founder impact 
    (%) and social media links as the others.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}\nHere are the known social media links for the founders:\n{social_media}"
