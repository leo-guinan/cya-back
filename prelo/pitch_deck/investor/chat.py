from prelo.models import PitchDeck
from prelo.pitch_deck.investor.competitor_analysis import ANALYSIS_TYPE, get_competitor_analysis
from submind.llms.submind import SubmindModelFactory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

def handle_quick_chat(message: str, deck: PitchDeck) -> str:
    if message == "Email Founders - Rejection Email":
        return email_founders_rejection_email()
    elif message == "Email Founders - Follow Up Email":
        return email_founders_follow_up_email()
    elif message == "Email Founders - Book a call":
        return email_founders_book_a_call()
    elif message == "Email Founders - Invite Co-Investors":
        return email_founders_invite_co_investors()
    elif message == "Email Founders - Request Info":
        return email_founders_request_info()
    elif message == "Share Concerns - Traction Concerns":
        return share_concerns_traction_concerns()
    elif message == "Share Concerns - Market Size Concerns":
        return share_concerns_market_size_concerns()
    elif message == "Share Concerns - Team Concerns":
        return share_concerns_team_concerns()
    elif message == "Share Concerns - Product Concerns":
        return share_concerns_product_concerns()
    elif message == "Share Concerns - Competitor Concerns":
        return share_concerns_competitor_concerns()
    elif message == "Share Concerns - Regulation Concerns":
        return share_concerns_regulation_concerns()
    elif message == "List Competitors - Competitor Matrix":
        return list_competitors_competitor_matrix(deck)
    elif message == "List Competitors - Key Differentiator":
        return list_competitors_key_differentiator(deck)
    elif message == "List Competitors - How Much They Raised":
        return list_competitors_how_much_they_raised(deck)
    elif message == "List Competitors - Competitor Market Share":
        return list_competitors_competitor_market_share()
    elif message == "List Competitors - Competitor Prices":
        return list_competitors_competitor_prices(deck)
    elif message == "List Competitors - Target Market":
        return list_competitors_target_market(deck)
    elif message == "Prepare questions - Competition Questions":
        return prepare_questions_competition_questions(deck)
    elif message == "Prepare questions - Go To Market Questions":
        return prepare_questions_go_to_market_questions()
    elif message == "Prepare questions - Traction Questions":
        return prepare_questions_traction_questions(deck)
    elif message == "Prepare questions - Team Questions":
        return prepare_questions_team_questions(deck)
    elif message == "Prepare questions - Shuffle Questions":
        return prepare_questions_shuffle_questions(deck)
    elif message == "Prepare questions - Moat Questions":
        return prepare_questions_moat_questions(deck)
    elif message == "Research Founders - Founder Social Media":
        return research_founders_founder_social_media(deck)
    elif message == "Research Founders - Founder Summary/Bio":
        return research_founders_founder_summary_bio(deck)
    elif message == "Research Founders - Due Dilligence":
        return research_founders_due_dilligence(deck)
    elif message == "Research Founders - Founder Domain Experience":
        return research_founders_founder_domain_experience(deck)
    elif message == "Research Founders - Why we rate the founder?":
        return research_founders_why_we_rate_the_founder(deck)
    elif message == "Generate Deal Memo - Standard Deal Memo":
        return generate_deal_memo_standard_deal_memo(deck)
    elif message == "Generate Deal Memo - With Option Pool Shuffle":
        return generate_deal_memo_with_option_pool_shuffle(deck)
    elif message == "Generate Deal Memo - With Non-Standard Liquidation Preferences":
        return generate_deal_memo_with_non_standard_liquidation_preferences(deck)
    return False

def email_founders_rejection_email(deck: PitchDeck) -> str:
    return "Dear Founders, we regret to inform you that we will not be moving forward with your proposal."

def email_founders_follow_up_email(deck: PitchDeck) -> str:
    return "Dear Founders, we would like to follow up on our previous conversation and discuss the next steps."

def email_founders_book_a_call(deck: PitchDeck) -> str:
    return "Dear Founders, please book a call with us at your earliest convenience to discuss further."

def email_founders_invite_co_investors(deck: PitchDeck) -> str:
    return "Dear Founders, we would like to invite our co-investors to join the discussion."

def email_founders_request_info(deck: PitchDeck) -> str:
    return "Dear Founders, could you please provide us with additional information regarding your proposal?"

def share_concerns_traction_concerns(deck: PitchDeck) -> str:
    return "We have some concerns regarding the traction of your product in the market."

def share_concerns_market_size_concerns(deck: PitchDeck) -> str:
    return "We have some concerns regarding the size of the market you are targeting."

def share_concerns_team_concerns(deck: PitchDeck) -> str:
    return "We have some concerns regarding the composition and experience of your team."

def share_concerns_product_concerns(deck: PitchDeck) -> str:
    return "We have some concerns regarding the viability and uniqueness of your product."

def share_concerns_competitor_concerns(deck: PitchDeck) -> str:
    return "We have some concerns regarding the competition in your market."

def share_concerns_regulation_concerns(deck: PitchDeck) -> str:
    return "We have some concerns regarding the regulatory environment for your product."

def list_competitors_competitor_matrix(deck: PitchDeck) -> str:
    return get_competitor_analysis(deck, "benefit")

def list_competitors_key_differentiator(deck: PitchDeck) -> str:
    return "Here are the key differentiators between you and your competitors."

def list_competitors_how_much_they_raised(deck: PitchDeck) -> str:
    return "Here is the information on how much funding your competitors have raised."

def list_competitors_competitor_market_share(deck: PitchDeck) -> str:
    return "Here is the market share of your competitors."

def list_competitors_competitor_prices(deck: PitchDeck) -> str:
    return "Here are the pricing details of your competitors."

def list_competitors_target_market(deck: PitchDeck) -> str:
    return "Here is the target market for your competitors."

def prepare_questions_competition_questions(deck: PitchDeck) -> str:
    return "Here are some questions to ask about the competition."

def prepare_questions_go_to_market_questions(deck: PitchDeck) -> str:
    return "Here are some questions to ask about the go-to-market strategy."

def prepare_questions_traction_questions(deck: PitchDeck) -> str:
    return "Here are some questions to ask about the traction of the product."

def prepare_questions_team_questions(deck: PitchDeck) -> str:
    return "Here are some questions to ask about the team."

def prepare_questions_shuffle_questions(deck: PitchDeck) -> str:
    return "Here are some shuffled questions to ask."

def prepare_questions_moat_questions(deck: PitchDeck) -> str:
    return "Here are some questions to ask about the moat of the product."

def research_founders_founder_social_media(deck: PitchDeck) -> str:
    return "Here is the social media information of the founders."

def research_founders_founder_summary_bio(deck: PitchDeck) -> str:
    return "Here is a summary and bio of the founders."

def research_founders_due_dilligence(deck: PitchDeck) -> str:
    return "Here is the due diligence information on the founders."

def research_founders_founder_domain_experience(deck: PitchDeck) -> str:
    return "Here is the domain experience of the founders."

def research_founders_why_we_rate_the_founder(deck: PitchDeck) -> str:
    return "Here is why we rate the founder."

def generate_deal_memo_standard_deal_memo(deck: PitchDeck) -> str:
    return "Here is the standard deal memo."

def generate_deal_memo_with_option_pool_shuffle(deck: PitchDeck) -> str:
    return "Here is the deal memo with option pool shuffle."

def generate_deal_memo_with_non_standard_liquidation_preferences(deck: PitchDeck) -> str:
    return "Here is the deal memo with non-standard liquidation preferences."


# def generate_response(message: str, prompt: str, context: object) -> str:
#     model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "write_memo")
#     prompt = ChatPromptTemplate.from_template(MEMO_PROMPT)
#     chain = prompt | model | StrOutputParser()
#     firm_id = pitch_deck_analysis.deck.s3_path.split("/")[-3]
#     investor_id = pitch_deck_analysis.deck.s3_path.split("/")[-2]
#     firm = InvestmentFirm.objects.get(lookup_id=firm_id)
#     investor = Investor.objects.get(lookup_id=investor_id)
#     submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
#     submind_document = remember(submind)
#     response = chain.invoke({
#         "mind": submind_document,
#         "firm_thesis": firm.thesis,
#         "investor_thesis": investor.thesis,
#         "summary": pitch_deck_analysis.summary,
#         "concerns": pitch_deck_analysis.concerns,
#         "believe": pitch_deck_analysis.believe,
#         "traction": pitch_deck_analysis.traction,
#     })