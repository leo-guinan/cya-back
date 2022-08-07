from client.models import ClientAccount
from feather.service import get_latest_data_for_twitter_account
from backend.celery import app


@app.task(name="daily_user_refresh")
def daily_refresh_of_users():
    #get list of client accounts on Feather
    #for each account that has groups, refresh accounts associated with that account
    accounts = ClientAccount.objects.filter(client__name="FEATHER").all()
    for account in accounts:
        get_latest_data_for_twitter_account(account)




def send_daily_subscriptions():
    pass

def send_weekly_subscriptions():
    pass

