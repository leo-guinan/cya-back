from backend.celery import app
from client.models import ClientAccount
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
