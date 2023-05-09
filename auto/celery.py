from __future__ import absolute_import
from celery import Celery
import os

from kombu import Queue, Exchange

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto.settings')

app = Celery('auto')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_queues = (
    Queue('priority', Exchange('priority'), routing_key='priority'),
    Queue('non_priority', Exchange('non_priority'), routing_key='non_priority'),
)

app.autodiscover_tasks()
