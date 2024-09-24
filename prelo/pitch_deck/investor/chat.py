from prelo.models import Investor, PitchDeck, PitchDeckAnalysis
from prelo.pitch_deck.investor.competitor_analysis import ANALYSIS_TYPE, get_competitor_analysis
from prelo.pitch_deck.investor.invite_coinvestor import write_invite_coinvestor
from prelo.pitch_deck.investor.meeting import write_meeting_email
from prelo.pitch_deck.investor.more_info import request_more_info
from prelo.pitch_deck.investor.rejection import write_rejection_email
from submind.llms.submind import SubmindModelFactory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from submind.memory.memory import remember
from submind.models import Submind


def generate_prompt(prompt_name: str, analysis: PitchDeckAnalysis, submind: Submind, **kwargs) -> str:
    model = SubmindModelFactory.get_mini(f"{prompt_name}_{analysis.deck.uuid}", prompt_name, temperature=0.0)
    mind = remember(submind)
    prompts = {
        "share_traction_concerns": """
            You are an investor submind whose goal is to 
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about writing down concerns 
            related to traction once you've reviewed a pitch deck. You have now just reviewed the traction slides for 
            the company. Write down in detail your concerns about the level of traction the company has. 
            Ban generic concerns and focus specifically on the concerns you have based on the company's pitch deck. 
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "share_market_size_concerns": """
            You are an investor submind whose goal is to 
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about writing down concerns 
            related to Market Size once you've reviewed a pitch deck. 
            You have now just reviewed the Market Size slides for the company. 
            Write down in detail your concerns about the size of the Market for the company. 
            Ban generic concerns and focus specifically on the concerns you have based on the company's pitch deck. 
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "share_team_concerns": """
            You are an investor submind whose goal is to 
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue.  You are passionate about writing down concerns 
            related to the ability of the founders to deliver what they share in their pitch deck.
            You have now just reviewed the Team slides for the company. 
            Write down in detail your concerns about the team of the company. 
            Ban generic concerns and focus specifically on the concerns you have based on the company's pitch deck. 
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "share_product_concerns": """
            You are an investor submind whose goal is to 
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about writing down concerns 
            related to a products ability to deliver what was shared in their pitch deck. 
            You have now just reviewed the Product slides for the company.  
            Write down in detail your concerns about the product state and technology to deliver what they have 
            shared in their pitch deck.
            Ban generic concerns and focus specifically on the concerns you have based on the company's pitch deck. 
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "share_competitor_concerns": """
            You are an investor submind whose goal is to  
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about sharing concerns 
            related to how the company will remain competitive with the top 5 competitors in their industry.  
            You have now just reviewed the Competitors slides for the company.
            Write down in detail your concerns about the work required for the company to separate itself from its competitors
            in order to achieve the expected milestones. Since you are an expert in the industry highlight other 
            competitors they have missed out from their pitch deck.
            Ban generic concerns and focus specifically on the concerns you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "share_regulation_concerns": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about writing down concerns 
            related to Regulation once you've reviewed a pitch deck. 
            You have now just reviewed the Regulation slides for the company.
            Write down in detail your concerns about the potential regulatory challenges that the company faces.
            Ban generic concerns and focus specifically on the concerns you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "prepare_competition_questions": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
            related to competition once you've reviewed a pitch deck. 
            You have now just reviewed the Competitors slides for the company.
            Write down in detail the questions you would ask the founders about their competition.
            Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "prepare_go_to_market_questions": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
            related to go-to-market strategy once you've reviewed a pitch deck. 
            You have now just reviewed the Go-To-Market slides for the company.
            Write down in detail the questions you would ask the founders about their go-to-market strategy.
            Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "prepare_traction_questions": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
            related to traction once you've reviewed a pitch deck. 
            You have now just reviewed the Traction slides for the company.
            Write down in detail the questions you would ask the founders about their traction.
            Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "prepare_team_questions": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
            related to the team once you've reviewed a pitch deck. 
            You have now just reviewed the Team slides for the company.
            Write down in detail the questions you would ask the founders about their team.
            Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "prepare_shuffle_questions": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
            related to various aspects of the company once you've reviewed a pitch deck. 
            You have now just reviewed the pitch deck for the company.
            Write down in detail the questions you would ask the founders about various aspects of their company.
            Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "prepare_moat_questions": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about preparing questions 
            related to the company's moat once you've reviewed a pitch deck. 
            You have now just reviewed the Moat slides for the company.
            Write down in detail the questions you would ask the founders about their moat.
            Ban generic questions and focus specifically on the questions you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "research_founder_social_media": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You've just finished reading the company's pitch deck. You know the LinkedIn and details of all the co-founders. 
            Can you share a short summary about each founder and include their LinkedIn and Twitter details. 
            Create a table Founder Social Media with the Founder names as column headers. Add rows for social media links 
            and short summaries.
            Here are the known social media links for the founders:
            {social_media}

            Here's the pitch deck:
            {pitch_deck}
        """,
        "research_founder_summary_bio": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You've done some early investigation on the founders of the company,
            you've also read the pitch deck and deeply understand the founders' backgrounds. 
            Share a short summary bio of each of the founders and articulate specifically how their 
            experiences will directly translate to the success of their startup.
            Here are the known social media links for the founders:
            {social_media}
            Here's the pitch deck:
            {pitch_deck}
        """,
    
        "research_founder_domain_experience": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You've done some early investigation on the founders of the company, 
            you've also read the pitch deck and deeply understand the founders' backgrounds. 
            Articulate very succinctly each founder's domain expertise and how it translates 
            to being useful for building a successful Startup in beehiiv. Include social media links.
            Create a table with the founder names as the headers and the 3 main rows as the founder expertise
            and social media links as the others.

            Here are the known social media links for the founders:
            {social_media}

            Here's the pitch deck:
            {pitch_deck}
        """,
        "research_founder_rating": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced startup researcher with 10 years experience of analyzing startup teams 
            and how their experience impacts the success of a startup. 
            Can you share each founder's percentage rating to indicate their importance to the Startup? 
            Include their social media links. 
            Create a table with the founder names as the headers and the 2 main rows as the founder impact 
            (%) and social media links as the others.

            Here are the known social media links for the founders:
            {social_media}

            Here's the pitch deck:
            {pitch_deck}
        """,
        "generate_deal_memo_deal_memo_template": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced pre-seed investor, you understand deeply how to assess early stage startups, 
            especially pre-seed startups with little or no revenue. You are passionate about generating deal memos 
            once you've reviewed a pitch deck. 
            You have now just reviewed the pitch deck for the company.
            Write down in detail the standard deal memo for the company.
            Ban generic information and focus specifically on the information you have based on the company's pitch deck.
            Draw from examples from the pitch deck.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "generate_deal_memo_generate_deal_memo": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced investor with 10 years experience investing in Startups like this one. 
            You specialize in writing deal memos based on your deep understanding of the pre-seed startup landscape.
            You appreciate that pre-seed startups have little or no revenue and barely have a product. 
            You have read the pitch deck for the company and you know their investment ask and their vision.
            Write a deal memo that you will be proud to share with co-investors. Ban generic deal memos,
            but follow a standard deal memo structure and make it specific to the company.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "generate_deal_memo_standard_term_sheet": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are an experienced investor with 10 years experience investing in Startups like this one. 
            You specialize in writing deal memos based on your deep understanding of the pre-seed startup landscape.
            You appreciate that pre-seed startups have little or no revenue and barely have a product. 
            You have read the pitch deck for the company and you know their investment ask and their vision.
            Write a deal memo that you will be proud to share with co-investors. Ban generic deal memos,
            but follow a standard deal memo structure and make it specific to the company.  

            Here's the pitch deck:
            {pitch_deck}
        """,
        "list_competitors_competitor_prices": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are a specialist in writing product reviews and creating competitive analysis matrix. 
            Create a competitor analysis table comparing the prices of the 5 top competitors. 
            List the prices for each product. 
            Make column headers the names of the competitors and price the rows under each column header the
            price of each competitor. Center the header and row values.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "list_competitors_competitor_matrix": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are a specialist in writing product reviews and creating competitive analysis matrix. 
            Create a competitor analysis table comparing the best features and benefits of [company] 
            against the 5 competitors. List the 5 major benefits and features that exists for [company] 
            but does not exist in all the other competitors. Make column 1 the benefits, 
            Make column 2 for [company] Allocate the other columns to the other 5 competitors.
            Center the header and row values.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "list_competitors_key_differentiator": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are a specialist in writing product reviews and creating competitive analysis matrix. 
            Articulate the key differentiator for [company] comparing it against the 5 top competitors. 
            try to find a similar feature for each of the other products. 
            Make column headers include [company] and the names of the competitors and key differentiator 
            rows under each column header stating why [company] is better than each competitor. 
            Ban generic features, focus on [company]. Center the header and row values.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "list_competitors_how_much_they_raised": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are a specialist in writing fundraising comparison reviews and creating competitive analysis matrix. 
            Create a competitor analysis table comparing the amount of funds raised by the 5 top competitors. 
            List the funding raised and stage for each competitor. 
            Make column headers the names of the competitors and make the rows under each column header the 
            Amount raised at each stage of each competitor's funding round.
            Center the header and row values.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "list_competitors_competitor_market_share": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are a specialist in writing market share reviews and creating competitive analysis matrix. 
            Create a competitor analysis table comparing the market share of the 5 top competitors. 
            List the market share for each product as a percentage. 
            Make column headers the names of the competitors and market the rows under each column header the
            percentage market share of each competitor.
            Center the header and row values.

            Here's the pitch deck:
            {pitch_deck}
        """,
        "list_competitors_target_market": """
            You are an investor submind whose goal is to    
            think the same way as the investor you have studied.

            Here's what you know about the thesis of the investor, their firm, 
            and what the investor values when looking at a company: {mind}
            You are a specialist in writing market share reviews and creating competitive analysis matrix. 
            Create a competitor analysis table comparing the target markets of the 5 top competitors. 
            List the target markets for each competitor. 
            Make column headers the names of the competitors and target market the rows under each column header the
            target market of each competitor. Center the header and row values.

            Here's the pitch deck:
            {pitch_deck}
        """,
    }
    prompt = ChatPromptTemplate.from_template(prompts[prompt_name])
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"pitch_deck": analysis.compiled_slides, "mind": mind, **kwargs}), "message"

def handle_quick_chat(message: str, deck: PitchDeck, investor: Investor, submind: Submind) -> str:
    if message == "Email Founders - Rejection Email":
        return write_rejection_email(deck.analysis, investor, submind)
    elif message == "Email Founders - Book a call":
        return write_meeting_email(deck.analysis, investor, submind)
    elif message == "Email Founders - Invite Co-Investors":
        return write_invite_coinvestor(deck.analysis, investor, submind)
    elif message == "Email Founders - Request Info":
        return request_more_info(deck.analysis, investor, submind)
    elif message == "Share Concerns - Traction Concerns":
        return share_concerns_traction_concerns(deck.analysis, submind)
    elif message == "Share Concerns - Market Size Concerns":
        return share_concerns_market_size_concerns(deck.analysis, submind)
    elif message == "Share Concerns - Team Concerns":
        return share_concerns_team_concerns(deck.analysis, submind)
    elif message == "Share Concerns - Product Concerns":
        return share_concerns_product_concerns(deck.analysis, submind)
    elif message == "Share Concerns - Competitor Concerns":
        return share_concerns_competitor_concerns(deck.analysis, submind)
    elif message == "Share Concerns - Regulation Concerns":
        return share_concerns_regulation_concerns(deck.analysis, submind)
    elif message == "List Competitors - Competitor Matrix":
        return list_competitors_competitor_matrix(deck.analysis, submind)
    elif message == "List Competitors - Key Differentiator":
        return list_competitors_key_differentiator(deck.analysis, submind)
    elif message == "List Competitors - How Much They Raised":
        return list_competitors_how_much_they_raised(deck.analysis, submind)
    elif message == "List Competitors - Competitor Market Share":
        return list_competitors_competitor_market_share(deck.analysis, submind)
    elif message == "List Competitors - Competitor Prices":
        return list_competitors_competitor_prices(deck.analysis, submind)
    elif message == "List Competitors - Target Market":
        return list_competitors_target_market(deck.analysis, submind)
    elif message == "Prepare questions - Competition Questions":
        return prepare_questions_competition_questions(deck.analysis, submind)
    elif message == "Prepare questions - Go To Market Questions":
        return prepare_questions_go_to_market_questions(deck.analysis, submind)
    elif message == "Prepare questions - Traction Questions":
        return prepare_questions_traction_questions(deck.analysis, submind)
    elif message == "Prepare questions - Team Questions":
        return prepare_questions_team_questions(deck.analysis, submind)
    elif message == "Prepare questions - Shuffle Questions":
        return prepare_questions_shuffle_questions(deck.analysis, submind)
    elif message == "Prepare questions - Moat Questions":
        return prepare_questions_moat_questions(deck.analysis, submind)
    elif message == "Research Founders - Founder Social Media":
        return research_founders_founder_social_media(deck.analysis, submind, social_media=deck.analysis.founder_summary)
    elif message == "Research Founders - Founder Summary/Bio":
        return research_founders_founder_summary_bio(deck.analysis, submind, social_media=deck.analysis.founder_summary)
    elif message == "Research Founders - Founder Domain Experience":
        return research_founders_founder_domain_experience(deck.analysis, submind, social_media=deck.analysis.founder_summary)
    elif message == "Research Founders - Why we rate the founder?":
        return research_founders_why_we_rate_the_founder(deck.analysis, submind, social_media=deck.analysis.founder_summary)
    elif message == "Generate Deal Memo - Standard Deal Memo":
        return generate_deal_memo_standard_deal_memo(deck.analysis, submind)
    return False, "error"

def share_concerns_traction_concerns(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("share_traction_concerns", analysis, submind)

def share_concerns_market_size_concerns(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("share_market_size_concerns", analysis, submind)

def share_concerns_team_concerns(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("share_team_concerns", analysis, submind)

def share_concerns_product_concerns(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("share_product_concerns", analysis, submind)

def share_concerns_competitor_concerns(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("share_competitor_concerns", analysis, submind)

def share_concerns_regulation_concerns(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("share_regulation_concerns", analysis, submind)

def list_competitors_competitor_matrix(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("list_competitors_competitor_matrix", analysis, submind)

def list_competitors_key_differentiator(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("list_competitors_key_differentiator", analysis, submind)

def list_competitors_how_much_they_raised(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("list_competitors_how_much_they_raised", analysis, submind)

def list_competitors_competitor_market_share(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("list_competitors_competitor_market_share", analysis, submind)

def list_competitors_competitor_prices(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("list_competitors_competitor_prices", analysis, submind)

def list_competitors_target_market(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("list_competitors_target_market", analysis, submind)

def prepare_questions_competition_questions(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("prepare_competition_questions", analysis, submind)

def prepare_questions_go_to_market_questions(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("prepare_go_to_market_questions", analysis, submind)

def prepare_questions_traction_questions(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("prepare_traction_questions", analysis, submind)

def prepare_questions_team_questions(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("prepare_team_questions", analysis, submind)

def prepare_questions_shuffle_questions(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("prepare_shuffle_questions", analysis, submind)

def prepare_questions_moat_questions(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("prepare_moat_questions", analysis, submind)

def research_founders_founder_social_media(analysis: PitchDeckAnalysis, submind: Submind, social_media: str) -> tuple[str, str]:
    return generate_prompt("research_founder_social_media", analysis, submind, social_media=social_media)

def research_founders_founder_summary_bio(analysis: PitchDeckAnalysis, submind: Submind, social_media: str) -> tuple[str, str]:
    return generate_prompt("research_founder_summary_bio", analysis, submind, social_media=social_media)

def research_founders_founder_domain_experience(analysis: PitchDeckAnalysis, submind: Submind, social_media: str) -> tuple[str, str]:
    return generate_prompt("research_founder_domain_experience", analysis, submind, social_media=social_media)

def research_founders_why_we_rate_the_founder(analysis: PitchDeckAnalysis, submind: Submind, social_media: str) -> tuple[str, str]:
    return generate_prompt("research_founder_rating", analysis, submind, social_media=social_media)

def generate_deal_memo_standard_deal_memo(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("generate_standard_deal_memo", analysis, submind)

def generate_deal_memo_with_option_pool_shuffle(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("generate_option_pool_shuffle_memo", analysis, submind)

def generate_deal_memo_with_non_standard_liquidation_preferences(analysis: PitchDeckAnalysis, submind: Submind) -> tuple[str, str]:
    return generate_prompt("generate_non_standard_liquidation_memo", analysis, submind)

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