from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'soleadify_ml.settings')

app = Celery('soleadify_ml')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
app.conf.task_default_queue = 'celery.fifo'

app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'tasks.extract_from_website.py.extract_contacts',
        'schedule': 5.0,
        'args': (16, 16)
    },
}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
