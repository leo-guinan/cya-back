import logging

from backend.celery import app
from followed.models import Subscriber
from followed.service import create_follower_record_for_subscriber, get_report_difference_and_email
logger = logging.getLogger(__name__)


@app.task(name='refresh_subscriber_followers')
def refresh_followers_for_account(subscriber_id):
    # do nothing anymore for the time being
    return
    # create_follower_record_for_subscriber(subscriber_id)

@app.task(name='refresh_all_subscriber_followers')
def refresh_followers():
    # do nothing anymore for the time being
    return
    # subscribers = Subscriber.objects.filter(beta=False).all()
    # for subscriber in subscribers:
    #     create_follower_record_for_subscriber(subscriber.id)

@app.task(name='refresh_all_beta_subscriber_followers')
def refresh_beta_followers():
    # do nothing anymore for the time being
    return
    # subscribers = Subscriber.objects.filter(beta=True).all()
    # for subscriber in subscribers:
    #     try:
    #         create_follower_record_for_subscriber(subscriber.id)
    #     except Exception as e:
    #         logger.error(e)

@app.task(name='send_report_emails')
def send_report_emails():
    # do nothing anymore for the time being
    return
    # subscribers = Subscriber.objects.filter(beta=False).all()
    # for subscriber in subscribers:
    #     get_report_difference_and_email(subscriber.id)

@app.task(name='send_beta_report_emails')
def send_beta_report_emails():
    # do nothing anymore for the time being
    return

    # subscribers = Subscriber.objects.filter(beta=True).all()
    # for subscriber in subscribers:
    #     try:
    #         get_report_difference_and_email(subscriber.id)
    #     except Exception as e:
    #         logger.error(e)