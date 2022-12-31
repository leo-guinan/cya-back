import json
import logging
import uuid
from datetime import datetime, timedelta
import pandas as pd
from sklearn.cluster import KMeans
from tqdm.notebook import tqdm
from sklearn.metrics import silhouette_score
import numpy as np
from pytz import utc

from enhancer.enhancers import twitter_account_analysis_prompt, ANALYSIS_PROMPT_STARTER, tweet_grouping_enhancer, \
    topic_summary
from enhancer.models import EnhancedTwitterAccount, EnhancedTweet, EnhancedTweetsGroup
from open_ai.api import OpenAIAPI
from twitter.models import TwitterAccount, Tweet
from twitter.service import get_bio_and_recent_tweets_for_account, get_twitter_account
logger = logging.getLogger(__name__)


def has_previous_analysis(enhanced_twitter_account):
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=7))
    previous_analysis = enhanced_twitter_account.enhancement_run_at and \
                        (enhanced_twitter_account.status == EnhancedTwitterAccount.EnhancedTwitterAccountAnalysisStatus.OKAY) and \
                        (enhanced_twitter_account.enhancement_run_at > date_to_compare_against)
    logger.debug(f'has previous analysis: {previous_analysis}')
    return previous_analysis


def get_analysis(twitter_id, client_account_id):
    parent_id = uuid.uuid4()
    logger.debug(f'getting analysis for twitter account: {twitter_id}')
    twitter_account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    if not twitter_account:
        twitter_account = get_twitter_account(twitter_id)
        if not twitter_account:
            logger.error(f'Unable to get twitter account for id: {twitter_id}')
            return None
    logger.debug(f'got twitter account: {twitter_account.id}')
    enhanced_twitter_account = EnhancedTwitterAccount.objects.filter(twitter_account=twitter_account).first()
    if not enhanced_twitter_account:
        enhanced_twitter_account = EnhancedTwitterAccount()
        enhanced_twitter_account.twitter_account = twitter_account
    if has_previous_analysis(enhanced_twitter_account):
        return enhanced_twitter_account
    recent_tweets, bio, is_likely_spam, saved_tweets = get_bio_and_recent_tweets_for_account(twitter_id, client_account_id)

    logger.debug(f'got bio and recent tweets for twitter account: {twitter_id}')
    if not is_likely_spam:
        if saved_tweets:
            groups = enhance_tweets(saved_tweets, parent_id  )
            summary = summarize_groups(groups, parent_id)
            enhanced_twitter_account.summary = summary
    else:
        enhanced_twitter_account.status = EnhancedTwitterAccount.EnhancedTwitterAccountAnalysisStatus.OKAY
        enhanced_twitter_account.likely_spam = True
        enhanced_twitter_account.summary = "This account is likely spam."
    enhanced_twitter_account.enhancement_run_at = utc.localize(datetime.now())
    enhanced_twitter_account.save()
    return enhanced_twitter_account


def enhance_twitter_account_with_summary(twitter_id, client_account_id):
    return get_analysis(twitter_id, client_account_id)

def enhance_tweet(tweet, parent_id):
    enhanced_tweet = EnhancedTweet.objects.filter(tweet=tweet).first()
    if not enhanced_tweet:
        enhanced_tweet = EnhancedTweet()
        enhanced_tweet.tweet = tweet
        tweet_embeddings = get_tweet_embeddings(tweet.message, parent_id)
        enhanced_tweet.embeddings = tweet_embeddings
        enhanced_tweet.save()
    return enhanced_tweet
def enhance_tweets(saved_tweets, parent_id):
    enhanced_tweets = []
    for saved_tweet in saved_tweets:
        enhanced_tweets.append(enhance_tweet(saved_tweet, parent_id))
    return group_and_categorize_tweets(enhanced_tweets, parent_id)

def get_tweet_embeddings(text, parent_id):
    openai_api = OpenAIAPI()
    return openai_api.embeddings(text, source="FOLLOWED", parent_id=parent_id)

def group_and_categorize_tweets(enhanced_tweets, parent_id):
    # df_tweets = pd.DataFrame([(tweet.text, tweet.public_metrics['like_count'], tweet.public_metrics['retweet_count'],
    #                            tweet.public_metrics['reply_count'], tweet.public_metrics['quote_count']) for tweet in
    #                           tweets], columns=['Tweet', 'Likes', 'Retweets', 'Replies', 'Quotes'])
    enhanced_tweets_df = pd.DataFrame([(enhanced_tweet.tweet.tweet_id, enhanced_tweet.tweet.message, enhanced_tweet.embeddings) for enhanced_tweet in enhanced_tweets], columns=['TweetId', 'Text', 'babbage_similarity'])
    enhanced_tweets_df.babbage_similarity.apply(np.array)
    matrix = np.vstack(enhanced_tweets_df.babbage_similarity.values)
    add_clusters(enhanced_tweets_df, matrix)
    groups = []
    for i in range(4):
        groups.append(categorize_grouping(enhanced_tweets_df[enhanced_tweets_df.Cluster == i], parent_id=parent_id))
    return groups


def add_clusters(df, matrix, n_clusters = 4):
    kmeans = KMeans(n_clusters=n_clusters, init="k-means++", random_state=42)
    kmeans.fit(matrix)
    labels = kmeans.labels_
    df["Cluster"] = labels
    # clusters = df.groupby("Cluster")
    # plot_results(matrix)

    return df

def categorize_grouping(df, parent_id):
    prompt = tweet_grouping_enhancer({d['TweetId']: d['Text'] for d in df.to_dict('records')})
    openai_api = OpenAIAPI()
    response = openai_api.complete(prompt, source="FOLLOWED", stop_tokens=['##END_TWEET##'], temperature=0, parent_id=parent_id)
    group = EnhancedTweetsGroup()
    group.enhancement_run_at = utc.localize(datetime.now())
    group.save()
    try:
        logger.debug(f'got response: {response}')
        parsed_response = json.loads(response, strict=False)
        logger.debug(f'parsed response: {parsed_response}')
        group.summary = parsed_response['shared_topics']
        for tweet in parsed_response['tweets']:
            enhanced_tweet = EnhancedTweet.objects.filter(tweet__tweet_id=tweet['tweet_id']).first()
            enhanced_tweet.category = tweet['topic']
            if tweet['sentiment'].lower() == 'positive':
                enhanced_tweet.sentiment = EnhancedTweet.EnhancedTweetSentiment.POSITIVE
            elif tweet['sentiment'].lower() == 'negative':
                enhanced_tweet.sentiment = EnhancedTweet.EnhancedTweetSentiment.NEGATIVE
            else:
                enhanced_tweet.sentiment = EnhancedTweet.EnhancedTweetSentiment.NEUTRAL
            enhanced_tweet.save()
            group.enhanced_tweets.add(enhanced_tweet)
    except json.decoder.JSONDecodeError as e:
        logger.error(e)
    group.save()
    return group

def summarize_groups(groups, parent_id):
    topic_summary_prompt = topic_summary([group.summary for group in groups])
    openai_api = OpenAIAPI()
    response = openai_api.complete(topic_summary_prompt, source="FOLLOWED", stop_tokens=['##END_TOPIC##'], temperature=0, parent_id=parent_id)
    return response