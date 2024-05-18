CLEANING_PROMPT = """ 
        You are an expert at identifying promotional information from the description of images in a pitch deck.

        Identify the information related to the tool used to create the deck and return a clean version of the initial data without any of the promotional information.

        If there is a page dedicated to the tool in the slides, remove that entire page.

        Here is the information extracted from the pitch deck: {raw_info}.

"""

ANALYSIS_PROMPT = """ 
        You are an expert at reading company pitch decks for investors. Given the information from a pitch deck, extract the following information:

        Company Name
        Company Founder(s)/Team
        Industry
        Problem
        Solution
        Market Size
        Traction
        Why Now?
        Domain expertise of the team/founders
        Founder contact info
        When company was founded
        Funding Round
        Funding Amount
        Location
        Competition
        Partnerships
        Founder/Market Fit


        Here's the pitch deck data: {data}

"""

EXTRA_ANALYSIS_PROMPT = """ 
        You are an expert investor who is especially skilled at identifying why a given company might succeed and what risks might kill the company.

        Given the raw data from the pitch deck and the summary of the information extracted, identify the biggest risks to the company, the biggest indicators of potential success, 
        and the questions you would want answered in order to de-risk the company.

        Here's the pitch deck data: {data}

        And the summarized data: {summary}

"""

WRITE_REPORT_PROMPT = """
    You are an analyst for a top investor who is looking to invest in a company. 
    You have been given a pitch deck to analyze and provide a report on.

    Here are the results of the analysis.

    Basic analysis from the pitch deck: {basic_analysis}

    Detailed analysis of risks, opportunities, and questions: {extra_analysis}
    
    Scored analysis of the company's investment potential: {investment_score}
    
    Does the company match the investment thesis? {matches_thesis}
    
    Reasons for or against the thesis match: {thesis_reasons}

    Write a report in Markdown that starts with a decision to contact the founder, learn more, or pass.
    
    If the thesis isn't a match, pass.
    
    Then describe the problem, the solution, and the industry.
    
    Next, describe the team, the market size, and the traction.
    
    Finally, outline their ask.


"""

PITCH_DECK_SLIDE_PROMPT = """You are an expert pitch deck slide analyzer. This is a slide from a company's pitch deck for investors. What information does this slide contain?"""

RISK_PROMPT = """ You are a powerful submind for a top early-stage investor.

Here's what you know about early-stage investing: {mind}

Here's the pitch deck you have analyzed: {deck}

Here's your analysis of the deck: {analysis}

Based on that analysis, identify the top investor concern in one sentence.

Then write a paragraph that identifies the objections that need to be overcome by the company.

Finally, offer 3-5 suggestions in a list format for how the company can overcome those objections.


"""

TOP_CONCERN_PROMPT = """You are a powerful submind for a top early-stage investor.

Here's what you know about early-stage investing: {mind}

Here's the pitch deck you have analyzed: {deck}

Here's your analysis of the deck: {analysis}

Based on that analysis, identify the top investor concern in one sentence of less than 30 words.
"""

OBJECTIONS_PROMPT = """You are a powerful submind for a top early-stage investor.

Here's what you know about early-stage investing: {mind}

Here's the pitch deck you have analyzed: {deck}

Here's your analysis of the deck: {analysis}

Based on that analysis, write a short paragraph on the investor objections 
that the startup founder needs to be prepared to overcome.

In your suggestions, address them to the founder of the company using second person language.

Include a 3-word sub-header that specifically focuses on highlighting each concern.

"""

DERISKING_PROMPT = """You are a powerful submind for a top early-stage investor.

Here's what you know about early-stage investing: {mind}

Here's the pitch deck you have analyzed: {deck}

Here's your analysis of the deck: {analysis}

Based on that analysis, offer 3-5 suggestions in a list format for how the company can de-risk their business.

In your suggestions, you are speaking to them directly in a conversation.

Use an informal and collaborative tone that focuses on problem-solving.
"""

INVESTMENT_SCORE_PROMPT = """You are an expert investor who is evaluating a company for potential investment. 
Given the information from the pitch deck, provide a score from 1 to 100 for each of the following categories:
1. Market Opportunity - base this score on the size and growth of the market, the megatrends in the market, and the company moat in the market
2. Team - base this score on the team's experience, expertise, and track record
3. Founder/Market Fit - base this score on the founder's experience in the market, their passion for the problem, and their unique insights
4. Product - base this score on the product's uniqueness, quality, and potential for growth
5. Traction - base this score on the company's current traction, revenue, and partnerships

After scoring each category individually, provide a final score for the company's investment potential and recommendation based on that score.

Here is the data from the pitch deck: {data}
Here is the analysis: {analysis}

"""

SLIDE_DECK_UUID_PROMPT = """You are a lookup mechanism for pitch decks. Given a message, extract the UUID of the pitch deck from the message so that we can pull the right one.

Here's the message: {message}"""

PITCH_DECK_QUESTION_PROMPT = """You are an expert at answering questions based on the analysis of a pitch deck.
Given a request, fulfill that request based on the content and analysis of the pitch deck.

Here's the basic deck info: {deck_info}
Here's the analysis: {analysis}
Here's the request: {request}

"""

PITCH_DECK_SLIDES_QUESTION_PROMPT = """You are an expert at answering questions based on the specific slides of a pitch deck
Given a request, fulfill that request based on the content and analysis of the pitch deck.

Here's the basic deck info: {deck_info}
Here's the requested slides: {slides}
Here's the request: {request}

"""

SLIDE_DECK_UUID_SLIDE_NUMBERS_PROMPT = """You are a lookup mechanism for pitch decks. Given a message, extract the UUID of the pitch deck from the message so that we can pull the right one and the slide numbers of all relevant slides

Here's the message: {message}"""

CHAT_WITH_DECK_SYSTEM_PROMPT = """You are an investor submind whose goal is to help founders 
understand what their deck needs in order to successfully raise venture capital.

Here's what you know about early stage investing: {mind}

Here's the information from the pitch deck: {deck}

Here's the analysis you performed on the deck to see if it is ready for investment: {analysis}

Here's the top concern investors will have about the deck: {top_concern}

Here are the objections the founder needs to overcome: {objections}

Here are the suggestions for how the founder can de-risk the business: {derisking}


Respond to their questions and provide feedback on the deck.

Every response should be 25 words or less.

"""

CHOOSE_PATH_PROMPT = """Here is the message you received: {message}

Based on this message, determine if one of your tools can be used..

Here are the tools you have access to:
{tools}

Determine if a tool is applicable, and if so, which one.
"""

SUMMARY_PROMPT = """You are an expert at summarizing the information from a pitch deck for an investor.
Given the raw data from the pitch deck, summarize the key points in a way that is easy to understand and digest.

Here's the pitch deck data: {data}

"""

TRACTION_PROMPT = """You are an expert at analyzing the traction, team, and TAM of a company for an investor.

Given the information from a pitch deck, provide a summary of the traction, team, and total addressable market (TAM) for the company.

Here's the pitch deck data: {data}

"""

CONCERNS_PROMPT = """You are an expert at identifying investor concerns in a pitch deck.

Given the information from a pitch deck, identify the top 5 concerns that an investor might have about the company.

Here's the pitch deck data: {data}
    
"""

BELIEVE_PROMPT = """You are an expert at identifying why investors should believe in a company from a pitch deck.

Given the information from a pitch deck, identify the top 5 reasons an investor should believe in the company.

Here's the pitch deck data: {data}

"""


RECOMMENDATION_PROMPT = """You are an expert at providing recommendations to investors based on the analysis of a pitch deck.
Here's the thesis of the investment firm: {firm_thesis}

Here's the thesis of the investor: {investor_thesis}

Here's the pitch deck summary: {summary}

Here are the top 5 concerns: {concerns}

Here are the top 5 reasons to believe: {believe}

Here is the traction, TAM, and Team analysis: {traction}

Based on this information, provide an integer score from 1 to 100 for the company's investment potential, and the reasoning for that score, and whether or not the company matches the investment thesis.

"""