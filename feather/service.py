from twitter.models import Group
from twitter.tasks import get_latest_tweets_for_account


def get_latest_data_for_twitter_account(account):
    #get groups owned by twitter account associated with client account
    groups = Group.objects.filter(owner=account.twitter_account).all()
    for group in groups:
        #get all accounts in group
        twitter_accounts = group.members.all()
        for twitter_account in twitter_accounts:
            get_latest_tweets_for_account.delay(account.id, twitter_account.twitter_id)