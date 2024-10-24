from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_competitor_matrix(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Creates a clear competitor analysis table
    2. Lists 5 major benefits and features for the company
    3. Compares these features against 5 competitors
    4. Uses appropriate column headers and row structure
    5. Provides specific, non-generic information based on the pitch deck
    6. Uses real competitor names and data, not generic names like "Competitor 1", "Competitor 2", etc.
    """

@validator(validate_competitor_matrix)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def list_competitors_competitor_matrix(mind: str, pitch_deck: str) -> str:
    """
    You are a specialist in writing product reviews and creating competitive analysis matrix. 
    Create a competitor analysis table comparing the best features and benefits of [company] 
    against the 5 competitors. List the 5 major benefits and features that exists for [company] 
    but does not exist in all the other competitors. Make column 1 the benefits, 
    Make column 2 for [company] Allocate the other columns to the other 5 competitors.
    Center the header and row values.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
