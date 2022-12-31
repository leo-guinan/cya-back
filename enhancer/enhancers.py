from enhancer.models import EnhancedTwitterAccount
from twitter.models import TwitterAccount


ANALYSIS_PROMPT_STARTER = """
{
    "summary": "
"""
def twitter_account_analysis_prompt(bio, tweets):
    prompt = f"""
    Given a group of tweets, create a summary of the tweets, identify the most prevalent topics in that group of tweets and whether the trending sentiment of the tweets is positive or negative.

    Respond in the following JSON format:
    {{
    "summary": "<summary>",
    "topics": [
    {{
    "topic": "<topic_1>",
    "how_often_present": <the percentage of example tweets this topic was referenced expressed as a value between 0.00 and 1.00">
    }},
    {{
    "topic": "<topic_2>",
    "how_often_present": <the percentage of example tweets this topic was referenced expressed as a value between 0.00 and 1.00">
    }},
    ...
    {{
    "topic": "<topic_n>",
    "how_often_present": <the percentage of example tweets this topic was referenced expressed as a value between 0.00 and 1.00">
    }}
    ]
    "sentiment": {{
    "positive": <true or false>,
    "strength": <integer value representing how negative or positive the tweets were overall, with 0 being neutral and 100 being very strongly negative or positive>
    }}
    }}
    Bio: 
    ##BEGIN_BIO##
    {bio}
    ##END_BIO##
    
    Tweets:
    ##BEGIN_TWEET## 
    {'''
    ##END_TWEET##
    
    ##BEGIN_TWEET##
    '''.join(tweets)}
    ##END_TWEET##
    
    The summary:
    {ANALYSIS_PROMPT_STARTER}
    
    """
    return prompt


def tweet_grouping_enhancer(tweets: dict):
    prompt = f"""
    Given a list of tweets, identify the common topic shared by the tweets in the list, the specific topic of each tweet, and the sentiment of each tweet, labeling it as "POSITIVE", "NEGATIVE", or "NEUTRAL".

    The tweets will be given in the following format:
    <tweet_id>: <text_of_the_tweet>

    Respond in the following JSON format:

    {{
    "shared_topics": "<identified_topics>",
        "tweets": [
    {{
    "tweet_id": "<id_of_the_tweet_given>",
    "topic": "<topic_of_the_tweet>",
    "sentiment": "<sentiment>"
    }}
    }}

    The tweets:
    {'##END_TWEET##'.join([f'{key}: {value}' for (key,value) in tweets.items()])}
    The Response:
    """
    return prompt

def topic_summary(summaries):
    prompt = f"""
Given the following topics that a user has tweeted about, summarize what they tend to talk about.

The topics:
{"##END_TOPIC##".join(summaries)}
The summary:

"""
    return prompt