from datetime import datetime, timedelta, date

import tweepy
from pytz import utc

from backend.celery import app
from client.exception import UnknownClientAccount
from client.models import ClientAccount, BetaAccount
from client.tasks import send_user_a_notification
from twitter.tasks import populate_user_data_from_twitter_id, unfollow_user_for_client_account
from twitter_api.twitter_api import TwitterAPI
from unfollow.models import AccountCheck, UnfollowRequest
from unfollow.service import get_twitter_account_info_for_check


@app.task(name="lookup_twitter_user", autoretry_for=(tweepy.errors.TooManyRequests,), retry_backoff=60,
          retry_kwargs={'max_retries': 8})
def lookup_twitter_user(client_account_id, force=False):
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    current_user = client_account.twitter_account

    if force or not current_user.last_checked or current_user.last_checked < (date.today() - timedelta(days=2)):
        populate_user_data_from_twitter_id.delay(current_user.twitter_id, client_account_id)
        current_user.last_checked = utc.localize(datetime.now())
        current_user.save()


@app.task(name="check_account")
def check_twitter_account(account_check_id):
    get_twitter_account_info_for_check(account_check_id)


@app.task(name="send_dms_to_beta_users")
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
Also, you can share your beta code with up to 4 friends, so feel free to pass it on if you know someone who might be interested!

Here’s your beta code to use:
{user.beta_code}'''
                                        )

        except Exception as e:
            print(f"Error sending DM: {e}")
            twitter_api.send_dm_to_user(1, "1325102346792218629",
                                        f"Error sending DM to {user.client_account.twitter_account.twitter_name}")

        user.messaged = True
        user.save()


@app.task(name="analyze_accounts_that_need_it")
def analyze_accounts_needing():
    checks = AccountCheck.objects.filter(last_analyzed__isnull=True).all()
    for check in checks:
        check_twitter_account.delay(check.id)


@app.task(name="unfollow_accounts")
def unfollow_accounts_needing():
    unfollow_requests = UnfollowRequest.objects.filter(unfollowed__isnull=True).all()
    for request in unfollow_requests:
        unfollow_user_for_client_account.delay(request.requesting_account.id, request.account_to_unfollow.twitter_id,
                                               request.id)


@app.task(name="notify_accounts_analysis_finished")
def notify_accounts():
    accounts_requesting_notified = ClientAccount.objects.filter(client__name="UNFOLLOW",
                                                                config__notification_requested=True).all()
    for account in accounts_requesting_notified:
        if AccountCheck.objects.filter(last_analyzed__isnull=True, account_id=account.id).count() == 0:
            send_user_a_notification(account.id,
                                     """Account analysis from @should_unfollow has finished.                                      
                                     View your results here: 
                                     https://app.whoshouldiunfollow.com/analyze""")
            account.config.notification_requested = False
            account.config.save()
