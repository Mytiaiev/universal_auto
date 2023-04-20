from __future__ import absolute_import
from celery import Celery
import os

from kombu import Queue, Exchange


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto.settings')

app = Celery('auto')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_queues = (
    Queue('priority_queue', Exchange('priority_queue'), routing_key='priority_queue'),
    Queue('non_priority_queue', Exchange('non_priority_queue'), routing_key='non_priority_queue'),
)

app.autodiscover_tasks()

