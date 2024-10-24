from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_founder_social_media(mind: str, pitch_deck: str, social_media: str) -> str:
    return """
    Evaluate if the output:
    1. Creates a clear table with founder names as column headers
    2. Includes rows for social media links (LinkedIn and Twitter)
    3. Provides a short summary about each founder
    4. Uses information from the pitch deck and provided social media links
    5. Presents the information in a clear and organized manner
    """

@validator(validate_founder_social_media)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def research_founders_founder_social_media(mind: str, pitch_deck: str, social_media: str) -> str:
    """
    You've just finished reading the company's pitch deck. You know the LinkedIn and details of all the co-founders. 
    Can you share a short summary about each founder and include their LinkedIn and Twitter details. 
    Create a table Founder Social Media with the Founder names as column headers. Add rows for social media links 
    and short summaries.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}\nHere are the known social media links for the founders:\n{social_media}"
