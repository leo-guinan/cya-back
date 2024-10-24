from decouple import config
from openai import OpenAI
import ell
from prelo.validator.decorator import validator

def validate_standard_deal_memo(mind: str, pitch_deck: str) -> str:
    return """
    Evaluate if the output:
    1. Follows a standard deal memo structure
    2. Provides comprehensive analysis of the investment opportunity
    3. Includes specific, non-generic information based on the pitch deck
    4. Demonstrates understanding of pre-seed startup assessment
    5. Aligns with the investor's mindset and values
    """

@validator(validate_standard_deal_memo)
@ell.simple(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')))
def generate_deal_memo_standard_deal_memo(mind: str, pitch_deck: str) -> str:
    """
    You are an experienced investor with 10 years experience investing in Startups like this one. 
    You specialize in writing deal memos based on your deep understanding of the pre-seed startup landscape.
    You appreciate that pre-seed startups have little or no revenue and barely have a product. 
    You have read the pitch deck for the company and you know their investment ask and their vision.
    Write a deal memo that you will be proud to share with co-investors. Ban generic deal memos,
    but follow a standard deal memo structure and make it specific to the company.
    """
    return f"Here's what you know about the thesis of the investor, their firm, and what the investor values when looking at a company: {mind}\nHere's the pitch deck:\n{pitch_deck}"
