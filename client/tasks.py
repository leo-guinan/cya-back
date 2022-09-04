from backend.celery import app
from client.models import ClientAccount, AccountConfig
from client.service import send_notification_email, send_notification_dm, send_notification_tweet
from twitter.tasks import populate_user_data_from_twitter_id
from twitter_api.twitter_api import TwitterAPI


@app.task(name='refresh_client_accounts')
def refresh_client_accounts():
    accounts = ClientAccount.objects.all()
    for account in accounts:
        try:
            populate_user_data_from_twitter_id(account.twitter_account.twitter_id, account.id)
        except:
            populate_user_data_from_twitter_id(account.twitter_account.twitter_id)


@app.task(name='refresh_client_twitter_tokens')
def refresh_client_twitter_tokens():
    accounts = ClientAccount.objects.all()
    twitter_api = TwitterAPI()
    for account in accounts:
        try:
            twitter_api.refresh_oauth2_token(account.id)
        except Exception as e:
            print(f"Error refreshing token: {e}")


@app.task(name='notify_user')
def send_user_a_notification(client_account_id_to_notify, message):
    account_config = AccountConfig.objects.filter(client_account_id=client_account_id_to_notify).first()
    if not account_config:
        account_config = AccountConfig()
        account_config.notification_preference = AccountConfig.NotificationPreference.TWEET
        account_config.client_account_id = client_account_id_to_notify
        account_config.save()
    client_account = ClientAccount.objects.filter(id=client_account_id_to_notify).first()

    if account_config.notification_preference == AccountConfig.NotificationPreference.TWEET:
        send_notification_tweet(client_account.twitter_account.twitter_id, message=message,
                                client=client_account.client)
    elif account_config.notification_preference == AccountConfig.NotificationPreference.DIRECT_MESSAGE:
        send_notification_dm(client_account.twitter_account.twitter_id, message=message, client=client_account.client)
    elif account_config.notification_preference == AccountConfig.NotificationPreference.EMAIL:
        send_notification_email(client_account.email, message, client=client_account.client)
