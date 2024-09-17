from prelo.models import Investor, PitchDeck
from prelo.pitch_deck.investor.competitor_analysis import ANALYSIS_TYPE, get_competitor_analysis
from prelo.pitch_deck.investor.followup import write_followup_email
from prelo.pitch_deck.investor.meeting import write_meeting_email
from prelo.pitch_deck.investor.more_info import request_more_info
from prelo.pitch_deck.investor.rejection import write_rejection_email
from submind.llms.submind import SubmindModelFactory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from submind.models import Submind

def handle_quick_chat(message: str, deck: PitchDeck, investor: Investor, submind: Submind) -> str:
    if message == "Email Founders - Rejection Email":
        return write_rejection_email(deck.analysis, investor, submind)
    elif message == "Email Founders - Follow Up Email":
        return write_followup_email(deck.analysis, investor, submind)
    elif message == "Email Founders - Book a call":
        return write_meeting_email(deck.analysis, investor, submind)
    elif message == "Email Founders - Invite Co-Investors":
        return email_founders_invite_co_investors(deck)
    elif message == "Email Founders - Request Info":
        return request_more_info(deck.analysis, investor, submind)
    elif message == "Share Concerns - Traction Concerns":
        return share_concerns_traction_concerns(deck)
    elif message == "Share Concerns - Market Size Concerns":
        return share_concerns_market_size_concerns(deck)
    elif message == "Share Concerns - Team Concerns":
        return share_concerns_team_concerns(deck)
    elif message == "Share Concerns - Product Concerns":
        return share_concerns_product_concerns(deck)
    elif message == "Share Concerns - Competitor Concerns":
        return share_concerns_competitor_concerns(deck)
    elif message == "Share Concerns - Regulation Concerns":
        return share_concerns_regulation_concerns(deck)
    elif message == "List Competitors - Competitor Matrix":
        return list_competitors_competitor_matrix(deck)
    elif message == "List Competitors - Key Differentiator":
        return list_competitors_key_differentiator(deck)
    elif message == "List Competitors - How Much They Raised":
        return list_competitors_how_much_they_raised(deck)
    elif message == "List Competitors - Competitor Market Share":
        return list_competitors_competitor_market_share(deck)
    elif message == "List Competitors - Competitor Prices":
        return list_competitors_competitor_prices(deck)
    elif message == "List Competitors - Target Market":
        return list_competitors_target_market(deck)
    elif message == "Prepare questions - Competition Questions":
        return prepare_questions_competition_questions(deck)
    elif message == "Prepare questions - Go To Market Questions":
        return prepare_questions_go_to_market_questions(deck)
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
    return get_competitor_analysis(deck, "funding")

def list_competitors_competitor_market_share(deck: PitchDeck) -> str:
    return get_competitor_analysis(deck, "market_share")

def list_competitors_competitor_prices(deck: PitchDeck) -> str:
    return get_competitor_analysis(deck, "pricing")

def list_competitors_target_market(deck: PitchDeck) -> str:
    return get_competitor_analysis(deck, "target_market")

def prepare_questions_competition_questions(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"competition_questions_{deck.uuid}", "prepare_competition_questions", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an experienced investor with 10 years experience investing in Startups like this one. You have read the pitch deck and you understand the competitive landscape of this vertical. Ask the founders 5 questions that will help you uncover the key benefits and unique value proposition that this company has over their competitors. You want to feel comfortable that the founders have a key differentiating factor that will appeal to their ideal customer before you invest?"""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def prepare_questions_go_to_market_questions(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"go_to_market_questions_{deck.uuid}", "prepare_go_to_market_questions", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an experienced investor with 10 years experience investing in Startups like this one. You have read the pitch deck and you understand their go to market strategy. Ask the founders 5 questions that will uncover key gaps you have seen in their go to market strategy. You want to feel comfortable that the founders have a strategic approach to their go to market strategy before you invest?"""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def prepare_questions_traction_questions(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"traction_questions_{deck.uuid}", "prepare_traction_questions", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an experienced investor with 10 years experience investing in Startups like this one. Ask the founders 5 questions that will make you feel comfortable that the founders have a clear plan for generating traction for this company?"""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({})

def prepare_questions_team_questions(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"team_questions_{deck.uuid}", "prepare_team_questions", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an experienced investor with 10 years experience investing in Startups like this one. You have read the pitch deck, since you invest in early stage startups you understand how important teams are to the success of early-stage startups. Ask 5 key questions that will make you feel comfortable that the co-founders have been through hard times together, know each other well and they are the right team to succeed with this particular idea?"""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def prepare_questions_shuffle_questions(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"shuffle_questions_{deck.uuid}", "prepare_shuffle_questions", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an experienced investor with 10 years experience investing in Startups like this one. You have read the pitch deck, since you invest in early stage startups. Based on the Moat Questions, Traction Questions, Go to Market Questions, Market Size Questions, Team Questions and Competition Questions Please create a random list of 7 questions to cover all of the above groups as a quick founder meeting preparation questions for me?"""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def prepare_questions_moat_questions(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"moat_questions_{deck.uuid}", "prepare_moat_questions", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an experienced investor with 10 years experience investing in Startups like this one. You have read the pitch deck, since you invest in early stage startups you understand how important Moat is to the success of early-stage startups. Ask 5 key questions that will make you feel comfortable that the co-founders have a specific Moat that sets them apart from everyone else trying to do something similar. Focus on moat questions that will guarantee success with this particular idea?"""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def research_founders_founder_social_media(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"founder_social_media_{deck.uuid}", "research_founder_social_media", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You've just finished reading the pitch deck. You know the linkedin and details of all the co-founders. Can you share a short summary about each founder and include their LinkedIn and Twitter details."""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def research_founders_founder_summary_bio(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"founder_summary_bio_{deck.uuid}", "research_founder_summary_bio", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You've done some early investigation on the founders, you've also read the pitch deck and deeply understand the founders' backgrounds. Share a short summary bio of each of the founders and articulate specifically how their experiences will directly translate to the success of their startup."""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def research_founders_due_dilligence(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"founder_due_diligence_{deck.uuid}", "research_founder_due_diligence", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """As an experienced investor, you're conducting due diligence on the founders. Based on the pitch deck and your research, provide a comprehensive due diligence report on the founders. Include their past experiences, successes, failures, and any potential red flags or notable achievements."""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def research_founders_founder_domain_experience(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"founder_domain_experience_{deck.uuid}", "research_founder_domain_experience", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You've done some early investigation on the founders, you've also read the pitch deck and deeply understand the founders' backgrounds. Articulate very succinctly each founder's domain expertise and how it translates to being useful for building a successful Startup. Include social media links"""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def research_founders_why_we_rate_the_founder(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"founder_rating_{deck.uuid}", "research_founder_rating", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """Can you share each founder's percentage rating to indicate their importance to the Startup? Include their social media links."""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def generate_deal_memo_standard_deal_memo(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"standard_deal_memo_{deck.uuid}", "generate_standard_deal_memo", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an expert investor with 10 years experience writing complex and simple deal memos. Share a standard deal memo to invest the full asking amount based on a post-money valuation that makes the full asking amount 10% of that post money valuation."""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def generate_deal_memo_with_option_pool_shuffle(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"option_pool_shuffle_memo_{deck.uuid}", "generate_option_pool_shuffle_memo", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an expert investor with 10 years experience writing complex deal memos. Create a deal memo that includes an option pool shuffle. Explain the implications of the option pool shuffle on the founders' ownership and the post-money valuation. Use the information from the pitch deck to make reasonable assumptions about the deal terms."""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})

def generate_deal_memo_with_non_standard_liquidation_preferences(deck: PitchDeck) -> str:
    model = SubmindModelFactory.get_mini(f"non_standard_liquidation_memo_{deck.uuid}", "generate_non_standard_liquidation_memo", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        """You are an expert investor with 10 years experience writing complex deal memos. Create a deal memo that includes non-standard liquidation preferences. Explain the implications of these preferences on potential exit scenarios. Use the information from the pitch deck to make reasonable assumptions about the deal terms and justify the need for non-standard liquidation preferences."""
    )
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": deck.analysis.compiled_slides})


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