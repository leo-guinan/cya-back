from mail.service import send_email
from twitter.models import TwitterAccount
from twitter.service import send_tweet, send_dm_to_account


def send_notification_email(email, message, client):
    send_email(to=email, message=message, subject="Who Should I Unfollow? Notification", client=client)

def send_notification_dm(twitter_id, message, client):
    send_dm_to_account(from_client=client, to_twitter_id=twitter_id, message=message)

def send_notification_tweet(twitter_id, message, client):
    twitter_account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    composite_message = f"@{twitter_account.twitter_username} {message}"
    send_tweet(from_client=client, message=composite_message)