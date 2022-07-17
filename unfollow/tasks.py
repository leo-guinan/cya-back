from datetime import datetime, timedelta

import tweepy
from celery import group
from pytz import utc
from django.utils import timezone

from backend.celery import app
from client.exception import UnknownClientAccount
from client.models import ClientAccount, BetaAccount
from twitter.models import TwitterAccount
from twitter_api.twitter_api import TwitterAPI
from unfollow.models import AnalysisReport, Analysis


@app.task(name="lookup_twitter_user", autoretry_for=(tweepy.errors.TooManyRequests,), retry_backoff=60,
          retry_kwargs={'max_retries': 8})
def lookup_twitter_user(client_account_id):
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    twitter_api = TwitterAPI()
    current_user = client_account.twitter_account
    analysis = Analysis.objects.filter(account=current_user).first()
    if not analysis:
        analysis = Analysis()
        analysis.account = current_user
        analysis.save()
    if analysis.state == Analysis.AnalysisState.REQUESTED or analysis.state == Analysis.AnalysisState.ERROR or (analysis.created < (
    utc.localize(datetime.now() - timedelta(days=7))) and analysis.state == Analysis.AnalysisState.COMPLETE):
        analysis.state = Analysis.AnalysisState.IN_PROGRESS
        analysis.save()
        followers = twitter_api.get_following_for_user(client_account_id=client_account_id)
        user_lookup_tasks = []
        analysis.following_count = len(followers)
        analysis.save()
        for user in followers:
            twitter_account = TwitterAccount.objects.filter(twitter_id=user.id).first()
            if not twitter_account:
                twitter_account = TwitterAccount(twitter_id=user.id, twitter_username=user.username,
                                                 twitter_name=user.name
                                                 )
                twitter_account.save()
            user_follows_account_lookup = TwitterAccount.objects.filter(twitter_id=current_user.twitter_id,
                                                                        follows__twitter_id=twitter_account.twitter_id).first()
            if not user_follows_account_lookup:
                user_follows_account.delay(client_account.twitter_account.twitter_id, user.id)

            user_lookup_tasks.append(
                get_most_recent_tweet_for_account.s(client_account_id, user.id))
        user_lookup_group = group(user_lookup_tasks)
        lookup_result = user_lookup_group()
        while not lookup_result.successful():
            if lookup_result.failed():
                analysis.state = Analysis.AnalysisState.ERROR
                analysis.save()
        date_to_compare_against = utc.localize(datetime.now() - timedelta(days=90))
        dormant_count = 0
        for relationship in current_user.follows.all():
            if relationship and relationship.last_tweet_date:
                if relationship.last_tweet_date < date_to_compare_against:
                    dormant_count += 1
        analysis.dormant_count = dormant_count
        analysis.state = Analysis.AnalysisState.COMPLETE
        analysis.save()


@app.task(name="lookup_twitter_user_nologin", autoretry_for=(tweepy.errors.TooManyRequests,), retry_backoff=60,
          retry_kwargs={'max_retries': 8})
def lookup_twitter_user_as_admin(twitter_id_to_check):
    twitter_api = TwitterAPI()
    current_user = TwitterAccount.objects.filter(twitter_id=twitter_id_to_check).first()
    if not current_user:
        user_data = twitter_api.lookup_user_as_admin(twitter_id=twitter_id_to_check)
        if not user_data:
            return None
        current_user = TwitterAccount(twitter_id=twitter_id_to_check, twitter_username=user_data.username,
                                      twitter_name=user_data.name)
        current_user.save()
    followers = twitter_api.get_following_for_user_admin(twitter_id=twitter_id_to_check)
    user_lookup_tasks = []
    user_follows_account_tasks = []
    for user in followers:
        twitter_account = TwitterAccount.objects.filter(twitter_id=user.id).first()
        if not twitter_account:
            twitter_account = TwitterAccount(twitter_id=user.id, twitter_username=user.username,
                                             twitter_name=user.name
                                             )
            twitter_account.save()
        user_follows_account_tasks.append(user_follows_account.s(twitter_id_to_check, user.id))
        user_lookup_tasks.append(get_most_recent_tweet_for_account_as_admin.s(user.id))
    user_lookup_group = group(user_lookup_tasks)
    user_follows_account_group = group(user_follows_account_tasks)
    follows = user_follows_account_group()
    res = user_lookup_group()
    while not res.successful() or not follows.successful():
        pass

    report_to_account.delay(current_user.twitter_id)


@app.task(name="get_most_recent_tweet", autoretry_for=(Exception,), retry_backoff=60,
          retry_kwargs={'max_retries': 8})
def get_most_recent_tweet_for_account(client_account_id, account_id):
    twitter_api = TwitterAPI()
    twitter_account = TwitterAccount.objects.filter(twitter_id=account_id).first()
    if (twitter_account.last_tweet_date and twitter_account.last_tweet_date > (
            utc.localize(datetime.now() - timedelta(days=90)))):
        return
    most_recent_tweet = twitter_api.get_most_recent_tweet_for_user(client_account_id=client_account_id,
                                                                   twitter_id=account_id)
    if most_recent_tweet is not None:
        twitter_account.last_tweet_date = most_recent_tweet.created_at
        twitter_account.save()
    else:
        # when no tweet, just set last tweet date to 5 years ago
        twitter_account.last_tweet_date = utc.localize(datetime.now() - timedelta(weeks=52 * 5))
        twitter_account.save()


@app.task(name="get_most_recent_tweet_nologin", autoretry_for=(tweepy.errors.TooManyRequests,), retry_backoff=60,
          retry_kwargs={'max_retries': 8})
def get_most_recent_tweet_for_account_as_admin(account_id):
    twitter_api = TwitterAPI()
    twitter_account = TwitterAccount.objects.filter(twitter_id=account_id).first()
    if (twitter_account.last_tweet_date and twitter_account.last_tweet_date > (
            utc.localize(datetime.now() - timedelta(days=90)))):
        return
    most_recent_tweet = twitter_api.get_most_recent_tweet_for_user_as_admin(account_id)
    if most_recent_tweet is not None:
        twitter_account.last_tweet_date = most_recent_tweet.created_at
        twitter_account.save()
    else:
        # when no tweet, just set last tweet date to 5 years ago
        twitter_account.last_tweet_date = utc.localize(datetime.now() - timedelta(weeks=52 * 5))
        twitter_account.save()


@app.task(name="user_follows_account")
def user_follows_account(user_id, follows_id):
    relationship = TwitterAccount.objects.filter(twitter_id=user_id,
                                                 follows__twitter_id=follows_id).first()
    if not relationship:
        current_user = TwitterAccount.objects.filter(twitter_id=user_id).first()
        twitter_account = TwitterAccount.objects.filter(twitter_id=follows_id).first()
        current_user.follows.add(twitter_account)
        current_user.save()


@app.task(name="send_analysis_to_account")
def report_to_account(twitter_id_to_check):
    twitter_api = TwitterAPI()
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=90))
    results = []
    current_user = TwitterAccount.objects.filter(twitter_id=twitter_id_to_check).first()
    print("Checking relationships...")
    for user_to_check in current_user.follows.all():

        if user_to_check and user_to_check.last_tweet_date:
            if user_to_check.last_tweet_date < date_to_compare_against:
                results.append(user_to_check)

    message = f".@{current_user.twitter_username} you follow {len(results)} accounts that haven't tweeted in the last three months"
    twitter_api.send_tweet(message)
    report = AnalysisReport(account=current_user, dormant_count=len(results),
                            following_count=current_user.follows.count())
    report.save()


@app.task(name="run_analysis_on_accounts_requesting")
def run_analysis():
    analyses_to_run = Analysis.objects.filter(state=Analysis.AnalysisState.REQUESTED).all()
    for analysis in analyses_to_run:
        client_account = ClientAccount.objects.filter(twitter_account=analysis.account).first()
        lookup_twitter_user.delay(client_account.id)

@app.task(name="run_analysis_on_accounts_errored")
def run_analysis_on_error():
    analyses_to_run = Analysis.objects.filter(state=Analysis.AnalysisState.ERROR).all()
    for analysis in analyses_to_run:
        client_account = ClientAccount.objects.filter(twitter_account=analysis.account).first()
        lookup_twitter_user.delay(client_account.id)

@app.task(name="send_dms_to_users")
def dm_users_who_ran_analysis():
    twitter_api = TwitterAPI()
    analyses_to_run = Analysis.objects.filter().all()
    for analysis in analyses_to_run:
        try:
            print(f"Sending DM to {analysis.account.twitter_name}")
            twitter_api.send_dm_to_user(analysis.account.twitter_id, "Testing DMs")
        except Exception as e:
            print(f"Error sending DM: {e}")


@app.task(name="send_dms_to_users")
def dm_beta_users():
    twitter_api = TwitterAPI()
    beta_users = BetaAccount.objects.filter(messaged=False).all()
    for user in beta_users:
        try:
            print(f"Sending DM to {user.client_account.twitter_account.twitter_name}")
            twitter_api.send_dm_to_user(1, user.client_account.twitter_account.twitter_id, f'''Thanks for your interest in beta testing Who Should I Unfollow? 

To get started, you can visit the site here: http://whoshouldiunfollow.com/

From there, log in with your Twitter account and click “Analyze My Account”. That will kick off the process. 
Ideally, that will finish running and you’ll be able to see the button for viewing the dormant accounts you follow, but I’m going to be monitoring the processes as they run to make sure they finish. Occasionally, they fail and I’ll need to kick it off again. If you let me know once you click analyze, I’ll make sure that your account finishes analyzing and shows you the dormant accounts you follow.

Here’s your beta code to use:
{user.beta_code}'''
                                        )

        except Exception as e:
            print(f"Error sending DM: {e}")
            twitter_api.send_dm_to_user(1, "1325102346792218629", f"Error sending DM to {user.client_account.twitter_account.twitter_name}")

        user.messaged = True
        user.save()