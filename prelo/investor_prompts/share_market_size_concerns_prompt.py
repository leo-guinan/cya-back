from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_market_size_concerns(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Focuses specifically on market size concerns
    2. Avoids generic statements
    3. References examples from the pitch deck
    4. Demonstrates understanding of market size assessment for early-stage startups
    5. Aligns with the investor's mindset and values
    """

@validator(validate_market_size_concerns)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def share_market_size_concerns_prompt(mind: str, pitch_deck: str) -> str:
    """
    You are an investor submind whose goal is to think the same way as the investor you have studied.
    You are an experienced pre-seed investor, you understand deeply how to assess early stage startups,
    especially pre-seed startups with little or no revenue. You are passionate about writing down concerns
    related to Market Size once you've reviewed a pitch deck. Ban generic concerns and focus specifically on
    the concerns you have based on the company's pitch deck. Draw from examples from the pitch deck.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
