from datetime import datetime

from client.models import Client
from followed.config import CLIENT_NAME
from followed.models import Subscriber, FollowerReport
from twitter.service import get_twitter_account
from twitter_api.twitter_api import TwitterAPI
from mail.service import send_email
CLIENT = Client.objects.filter(name=CLIENT_NAME).first()


def create_follower_record_for_subscriber(subscriber_id):
    twitter_api = TwitterAPI(client=CLIENT)
    subscriber = Subscriber.objects.filter(id=subscriber_id).first()
    if not subscriber:
        return None
    twitter_id = subscriber.client_account.twitter_account.twitter_id
    client_account_id = subscriber.client_account.id
    follower_report = FollowerReport()
    follower_report.subscriber = subscriber
    follower_report.date = datetime.now()
    follower_report.save()
    followers = twitter_api.get_users_following_account(twitter_id=twitter_id, client_account_id=client_account_id)
    for user in followers:
        twitter_account = get_twitter_account(user.id, client_account_id)
        follower_report.followers.add(twitter_account)
    follower_report.save()


def get_report_difference_and_email(subscriber_id):
    subscriber = Subscriber.objects.filter(id=subscriber_id).first()
    if not subscriber:
        return None
    reports = subscriber.reports.all()
    if len(reports) < 2:
        return None
    current_report = reports[len(reports) - 1]
    previous_report = reports[len(reports) - 2]
    current_followers = [{"id": follower.twitter_id, "name": follower.twitter_username, "bio": follower.twitter_bio} for follower in current_report.followers.all() ]
    previous_followers = [{"id": follower.twitter_id, "name": follower.twitter_username, "bio": follower.twitter_bio} for follower in previous_report.followers.all()]
    new_followers = [follower for follower in current_followers if follower not in previous_followers]
    lost_followers = [follower for follower in previous_followers if follower not in current_followers]
    send_email(subscriber.client_account.email, "New Followers: " + "\n".join(map(lambda x: f"{x['name'] if x['name'] else str(x['id'])}\n{x['bio']}\n",new_followers)) + "\n\nLost Followers:\n\n"+",".join(map(lambda x: f"{x['name'] if x['name'] else str(x['id'])}\n{x['bio']}\n",lost_followers)), "New Followers")
    return new_followers, lost_followers

