from backend.celery import app
from client.models import ClientAccount
from twitter.tasks import populate_user_data_from_twitter_id


@app.task(name='refresh_client_accounts')
def refresh_client_accounts():
    accounts = ClientAccount.objects.all()
    for account in accounts:
        try:
            populate_user_data_from_twitter_id(account.twitter_account.twitter_id, account.id)
        except:
            populate_user_data_from_twitter_id(account.twitter_account.twitter_id)
