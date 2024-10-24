from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_key_differentiator(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Clearly articulates the key differentiator for the company
    2. Compares against 5 top competitors
    3. Uses appropriate column headers and row structure
    4. Provides specific, non-generic information based on the pitch deck
    5. Focuses on why the company is better than each competitor
    6. Uses real competitor names and data, not generic names like "Competitor 1", "Competitor 2", etc.
    """

@validator(validate_key_differentiator)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def list_competitors_key_differentiator(mind: str, pitch_deck: str) -> str:
    """
    You are a specialist in writing product reviews and creating competitive analysis matrix. 
    Articulate the key differentiator for [company] comparing it against the 5 top competitors. 
    Try to find a similar feature for each of the other products. 
    Make column headers include [company] and the names of the competitors and key differentiator 
    rows under each column header stating why [company] is better than each competitor. 
    Ban generic features, focus on [company]. Center the header and row values.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
