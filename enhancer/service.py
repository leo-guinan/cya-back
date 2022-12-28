import json
import logging
from datetime import datetime, timedelta

from pytz import utc

from enhancer.enhancers import twitter_account_analysis_prompt, ANALYSIS_PROMPT_STARTER
from enhancer.models import EnhancedTwitterAccount
from open_ai.api import OpenAIAPI
from twitter.models import TwitterAccount
from twitter.service import get_bio_and_recent_tweets_for_account, get_twitter_account
logger = logging.getLogger(__name__)


def has_previous_analysis(enhanced_twitter_account):
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=7))
    previous_analysis = enhanced_twitter_account.enhancement_run_at and \
                        (enhanced_twitter_account.status == EnhancedTwitterAccount.EnhancedTwitterAccountAnalysisStatus.OKAY) and \
                        (enhanced_twitter_account.enhancement_run_at > date_to_compare_against)
    logger.debug(f'has previous analysis: {previous_analysis}')
    return previous_analysis


def account_is_likely_spam(bio, recent_tweets):
    return not bio or not recent_tweets or len(recent_tweets) < 5 or len(bio) < 10


def get_analysis(twitter_id, client_account_id):
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
    recent_tweets, bio = get_bio_and_recent_tweets_for_account(twitter_id, client_account_id)
    logger.debug(f'got bio and recent tweets for twitter account: {twitter_id}')
    if not account_is_likely_spam(bio, recent_tweets):
        logger.debug(f'account is not likely spam, running analysis')
        openai_api = OpenAIAPI()
        prompt = twitter_account_analysis_prompt(bio, recent_tweets)
        raw_analysis = openai_api.complete(prompt, source="FOLLOWED", stop_tokens=['##END_TWEET##', '##END_BIO##'], temperature=0)
        logger.debug(f'got raw analysis: {raw_analysis}')
        try:
            analysis = json.loads(ANALYSIS_PROMPT_STARTER + raw_analysis, strict=False)
            enhanced_twitter_account.analysis = analysis
            enhanced_twitter_account.status = EnhancedTwitterAccount.EnhancedTwitterAccountAnalysisStatus.OKAY
        except json.decoder.JSONDecodeError as e:
            # TODO: fix json with openai
            logger.error(e)
            logger.debug(ANALYSIS_PROMPT_STARTER + raw_analysis)
            analysis = {
                "error": e.msg,
                "summary": "There was an error with the analysis. Please send @leo_guinan a DM and let him know you received this error."
            }
            enhanced_twitter_account.analysis = analysis
            enhanced_twitter_account.status = EnhancedTwitterAccount.EnhancedTwitterAccountAnalysisStatus.ERROR

        enhanced_twitter_account.summary = analysis['summary']
    else:
        enhanced_twitter_account.status = EnhancedTwitterAccount.EnhancedTwitterAccountAnalysisStatus.OKAY
        enhanced_twitter_account.likely_spam = True
        enhanced_twitter_account.summary = "This account is likely spam."
    enhanced_twitter_account.enhancement_run_at = utc.localize(datetime.now())
    enhanced_twitter_account.save()
    return enhanced_twitter_account


def enhance_twitter_account_with_summary(twitter_id, client_account_id):
    return get_analysis(twitter_id, client_account_id)
