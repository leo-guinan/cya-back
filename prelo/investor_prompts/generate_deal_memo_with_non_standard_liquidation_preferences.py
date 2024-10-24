from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_deal_memo_non_standard_liquidation(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Addresses non-standard liquidation preferences in detail
    2. Explains the impact on deal structure and potential outcomes
    3. Provides specific, non-generic information based on the pitch deck
    4. Demonstrates understanding of liquidation preference structures
    5. Aligns with the investor's mindset and values
    """

@validator(validate_deal_memo_non_standard_liquidation)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def generate_deal_memo_with_non_standard_liquidation_preferences(mind: str, pitch_deck: str) -> str:
    """
    You are an experienced investor specializing in deal memos for startups with non-standard liquidation preferences.
    You understand the implications of various liquidation preference structures on investor returns and founder incentives.
    Write a detailed deal memo that addresses the non-standard liquidation preferences, their impact on the deal structure,
    and how they affect potential outcomes for all stakeholders. Be specific to the company and avoid generic statements.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
