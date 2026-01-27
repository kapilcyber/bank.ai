from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "techbank_workers",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    # Redis connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_connection_retry_delay=2.0,  # seconds
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        },
        'socket_connect_timeout': 5,
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'health_check_interval': 30,
    },
    broker_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        },
        'socket_connect_timeout': 5,
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'health_check_interval': 30,
    },
)

if __name__ == '__main__':
    celery_app.start()


