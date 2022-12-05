from backend.celery import app
from followed.models import Subscriber
from followed.service import create_follower_record_for_subscriber, get_report_difference_and_email


@app.task(name='refresh_subscriber_followers')
def refresh_followers():
    subscribers = Subscriber.objects.all()
    for subscriber in subscribers:
        create_follower_record_for_subscriber(subscriber.id)



@app.task(name='send_report_emails')
def send_report_emails():
    subscribers = Subscriber.objects.all()
    for subscriber in subscribers:
        get_report_difference_and_email(subscriber.id)