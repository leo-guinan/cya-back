from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_competitor_prices(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Creates a clear table comparing prices of 5 top competitors
    2. Lists prices for each product
    3. Uses appropriate column headers and row structure
    4. Provides specific, non-generic information based on the pitch deck
    5. Centers the header and row values
    6. Uses real competitor names and prices, not generic names like "Competitor 1", "Competitor 2", etc.
    """

@validator(validate_competitor_prices)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def list_competitors_competitor_prices(mind: str, pitch_deck: str) -> str:
    """
    You are a specialist in writing product reviews and creating competitive analysis matrix. 
    Create a competitor analysis table comparing the prices of the 5 top competitors. 
    List the prices for each product. 
    Make column headers the names of the competitors and price the rows under each column header the
    price of each competitor. Center the header and row values.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
