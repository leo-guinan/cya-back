from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_deal_memo_option_pool_shuffle(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Addresses the option pool shuffle in detail
    2. Explains the impact on deal terms and valuations
    3. Provides specific, non-generic information based on the pitch deck
    4. Demonstrates understanding of option pool dynamics
    5. Aligns with the investor's mindset and values
    """

@validator(validate_deal_memo_option_pool_shuffle)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def generate_deal_memo_with_option_pool_shuffle(mind: str, pitch_deck: str) -> str:
    """
    You are an experienced investor specializing in deal memos for startups with option pool shuffles.
    You understand the implications of option pool shuffles on deal terms and valuations.
    Write a detailed deal memo that addresses the option pool shuffle, its impact on the deal structure,
    and how it affects the overall valuation and equity distribution. Be specific to the company and avoid generic statements.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
