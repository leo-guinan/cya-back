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

CELERY_TASK_ROUTES = {
 'unfollow.tasks.*': {'queue': 'default'},
 'client.tasks.*': {'queue': 'default'},
 'crawler.tasks.*': {'queue': 'default'},
 'feather.tasks.*': {'queue': 'default'},
 'twitter.tasks.*': {'queue': 'default'},
 'watchtweet.tasks.*': {'queue': 'default'},
 'friendcontent.tasks.*': {'queue': 'bot'},
}

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
        'options': {'queue': 'default'}
    },
    'analyze_accounts': {
        'task': 'analyze_accounts_that_need_it',
        'schedule': crontab(hour='*'),
        'options': {'queue': 'default'}

    },
    'unfollow_accounts': {
        'task': 'unfollow_accounts',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'default'}

    },
    'daily_user_refresh': {
        'task': 'daily_user_refresh',
        'schedule': crontab(hour=0),
        'options': {'queue': 'default'}

    },
    'update_accounts_missing_data': {
        'task': 'populate_account_data',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'default'}
    },
    'notify_unfollow_analysis_complete': {
        'task': 'notify_accounts_analysis_finished',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'default'}
    },
    'weekly_update_followers': {
        'task': 'refresh_all_subscriber_followers',
        'schedule': crontab(hour=0, minute=0, day_of_week='sun'),
        'options': {'queue': 'default'}
    },
    'daily_update_followers': {
        'task': 'refresh_all_beta_subscriber_followers',
        'schedule': crontab(hour=0, minute=0, day_of_week='*'),
        'options': {'queue': 'default'}
    },
    'hourly_process_transcripts': {
        'task': 'effortless_reach.transcribe_all_podcasts',
        'schedule': crontab(hour='*', minute=0),
        'options': {'queue': 'default'}
    },
    'daily_convert_files': {
        'task': 'effortless_reach.convert_needed_files',
        'schedule': crontab(hour=0, minute=0),
        'options': {'queue': 'default'}
    }

}
