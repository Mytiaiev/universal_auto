from __future__ import absolute_import
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto.settings')

app = Celery('auto')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
