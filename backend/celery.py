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
    'weekly_update_email': {
        'task': 'coach.tasks.send_weekly_prompts',
        'schedule': crontab(hour='17', minute='0', day_of_week='mon'),
    },
    'daily_checkin_email': {
        'task': 'coach.tasks.send_daily_checkins',
        'schedule': crontab(hour='13', minute='0'),
    },
    'check_inbox': {
        'task': 'personal.tasks.look_for_new_messages',
        'schedule': crontab(hour='*', minute='*/5'),
    },


}
