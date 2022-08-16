import os

from celery import Celery
from celery.schedules import crontab
from decouple import config

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
BASE_REDIS_URL = config('REDIS_URL')

app = Celery('backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
app.conf.broker_url = BASE_REDIS_URL
app.conf.beat_scheduler = 'django_celery_beat.schedulers.DatabaseScheduler'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {
    # 'analyze_requested': {
    #     'task': 'run_analysis_on_accounts_requesting',
    #     'schedule': crontab(hour='*', minute=30),
    # },
    # 'analyse_errored': {
    #     'task': 'run_analysis_on_accounts_errored',
    #     'schedule': crontab(hour='*', minute=0),
    # },
    'message_beta_users': {
        'task': 'send_dms_to_beta_users',
        'schedule': crontab(hour='*', minute=0),
    },
    'analyze_accounts': {
        'task': 'analyze_accounts_that_need_it',
        'schedule': crontab(hour='*')
    },
    'unfollow_accounts': {
        'task': 'unfollow_accounts',
        'schedule': crontab(minute='*/15')
    },
    # 'refresh_twitter_tokens': {
    #     'task': 'refresh_client_twitter_tokens',
    #     'schedule': crontab(hour='*', minute=42)
    # }
    # 'watch_mentions': {
    #     'task': 'handle_tweet',
    #     'schedule': crontab(hour='*')
    # },
    'process_triggers': {
        'task': 'process_tweets',
        'schedule': crontab(hour='*')
    },
    'daily_user_refresh': {
        'task': 'daily_user_refresh',
        'schedule': crontab(hour=0)
    }
}
