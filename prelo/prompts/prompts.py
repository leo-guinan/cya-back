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

    Write a report in Markdown that starts with a decision to contact the founder, learn more, or pass.
    
    Then describe the problem, the solution, and the industry.
    
    Next, describe the team, the market size, and the traction.
    
    Finally, outline their ask.


"""

PITCH_DECK_SLIDE_PROMPT = """You are an expert pitch deck slide analyzer. This is a slide from a company's pitch deck for investors. What information does this slide contain?"""

INVESTMENT_SCORE_PROMPT = """You are an expert investor who is evaluating a company for potential investment. 
Given the information from the pitch deck, provide a score from 1 to 10 for each of the following categories:
1. Market Opportunity - base this score on the size and growth of the market, the megatrends in the market, and the company moat in the market
2. Team - base this score on the team's experience, expertise, and track record
3. Founder/Market Fit - base this score on the founder's experience in the market, their passion for the problem, and their unique insights
4. Product - base this score on the product's uniqueness, quality, and potential for growth
5. Traction - base this score on the company's current traction, revenue, and partnerships

After scoring each category individually, provide a final score for the company's investment potential and recommendation based on that score.

Here is the data from the pitch deck: {data}
Here is the analysis: {analysis}

"""