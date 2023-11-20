from __future__ import absolute_import
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto.settings')

app = Celery('auto')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_queues = {
    'beat_tasks': {
        'exchange': 'beat_tasks',
        'routing_key': 'beat_tasks',
    },
    'bot_tasks': {
        'exchange': 'bot_tasks',
        'routing_key': 'bot_tasks',
    },
}

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    timezone='Europe/Kiev',
    worker_heartbeat_interval=25,
    task_prefetch_multiplier=1,
    redis_max_connections=50,
    broker_transport_options={
                                'visibility_timeout': 1800,
                                'health_check_interval': 10,
                                'max_retries': 3,
                                'max_connections': 50,
                                'retry_on_timeout': True,
                                'connection_retry': True,
                                'connection_timeout': 120,
                                'connection_max_retries': 0,
                                'socket_keepalive': True,
                                'socket_timeout': 10,
                                'socket_connect_timeout': 60
                                }
)

app.autodiscover_tasks(['auto'])
