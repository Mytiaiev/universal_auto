from __future__ import absolute_import
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto.settings')

app = Celery('auto')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_send_sent_event = True
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
)

app.autodiscover_tasks()
