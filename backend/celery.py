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
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {

    'complete-goals-1-minute': {
        'task': 'submind.tasks.complete_goals',
        'schedule': crontab(minute='*/1'),
    },
    'check-decks-1-minute': {
        'task': 'prelo.tasks.check_for_decks',
        'schedule': crontab(minute='*/1'),
    },
    'check-messages-1-minute': {
        'task': 'prelo.tasks.resend_messages',
        'schedule': crontab(minute='*/1'),
    },
    'cleanup-messages-to-confirm-hourly': {
        'task': 'prelo.tasks.cleanup_messages_to_confirm',
        'schedule': crontab(minute=0, hour='*/1'),  # Run at the start of every hour
    },

}
