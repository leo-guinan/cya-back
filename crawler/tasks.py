from backend.celery import app
from twitter.models import TwitterAccount
from twitter_api.twitter_api import TwitterAPI


# @app.task(name="crawl_account")
def start_crawl(twitter_id, number_of_steps):
    # get followers
    twitter_api = TwitterAPI()
    current_account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    if not current_account:
        user_data = twitter_api.lookup_user_as_admin(twitter_id)
        current_account = TwitterAccount(twitter_id=user_data.id, twitter_username=user_data.username,
                                             twitter_name=user_data.name, twitter_bio=user_data.description)
        current_account.save()
    following = twitter_api.get_following_for_user_admin(twitter_id)
    for follower in following:
        twitter_account = TwitterAccount.objects.filter(twitter_id=follower.id).first()
        if not twitter_account:
            twitter_account = TwitterAccount(twitter_id=follower.id, twitter_username=follower.username,
                                             twitter_name=follower.name, twitter_bio=follower.description
                                             )
            twitter_account.save()
            current_account.follows.add(twitter_account)
            twitter_account.save()

    followers = twitter_api.get_followers_for_user_admin(twitter_id)
    for follower in followers:
        twitter_account = TwitterAccount.objects.filter(twitter_id=follower.id).first()
        if not twitter_account:
            twitter_account = TwitterAccount(twitter_id=follower.id, twitter_username=follower.username,
                                             twitter_name=follower.name, twitter_bio=follower.description
                                             )
            twitter_account.save()
            twitter_account.follows.add(current_account)
            twitter_account.save()
    if number_of_steps > 1:
        for follower in following:
            start_crawl.delay(follower.id, number_of_steps - 1)
        # get following
        for follower in followers:
            start_crawl.delay(follower.id, number_of_steps - 1)
