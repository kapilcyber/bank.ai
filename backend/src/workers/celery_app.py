"""Celery application configuration."""
from celery import Celery
from celery.signals import worker_process_init
from src.config.celery_config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from src.utils.logger import get_logger
import sys

logger = get_logger(__name__)


def check_redis_connection():
    """Check if Redis is available and provide helpful error message if not."""
    try:
        import redis
        from urllib.parse import urlparse
        
        # Parse Redis URL
        parsed = urlparse(CELERY_BROKER_URL)
        host = parsed.hostname or 'localhost'
        port = parsed.port or 6379
        
        # Try to connect
        r = redis.Redis(host=host, port=port, socket_connect_timeout=2, decode_responses=False)
        r.ping()
        logger.info(f"Successfully connected to Redis at {host}:{port}")
        return True
    except ImportError:
        logger.error("Redis Python package not installed. Install it with: pip install redis")
        return False
    except Exception as e:
        error_msg = str(e)
        if "10061" in error_msg or "actively refused" in error_msg.lower():
            logger.error(
                "\n" + "="*70 + "\n"
                "Redis is not running or not accessible!\n\n"
                "To fix this issue:\n"
                "1. Install Redis:\n"
                "   - Windows: Download from https://github.com/microsoftarchive/redis/releases\n"
                "   - Or use WSL: wsl sudo apt-get install redis-server\n"
                "   - Or use Docker: docker run -d -p 6379:6379 redis:latest\n\n"
                "2. Start Redis:\n"
                "   - Windows: Run redis-server.exe\n"
                "   - WSL: sudo service redis-server start\n"
                "   - Docker: Already running if using Docker\n\n"
                "3. Verify Redis is running:\n"
                "   - Test connection: redis-cli ping (should return PONG)\n\n"
                "Current Redis URL: " + CELERY_BROKER_URL + "\n"
                + "="*70 + "\n"
            )
        else:
            logger.error(f"Failed to connect to Redis: {e}")
        return False


# Create Celery app
celery_app = Celery(
    "techbank_workers",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['src.workers.tasks']
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
    # Redis connection settings - more aggressive retry settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=3,  # Reduced from 10 to fail faster
    broker_connection_retry_delay=2.0,  # seconds
    # Shorter timeouts for faster failure detection
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 2.0  # Reduced from 5.0
        },
        'socket_connect_timeout': 2,  # Reduced from 5
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'health_check_interval': 30,
    },
    broker_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 2.0  # Reduced from 5.0
        },
        'socket_connect_timeout': 2,  # Reduced from 5
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'health_check_interval': 30,
    },
)


@worker_process_init.connect
def check_redis_on_startup(**kwargs):
    """Check Redis connection when worker process starts."""
    logger.info("Worker process initializing, checking Redis connection...")
    if not check_redis_connection():
        logger.error("Cannot start Celery worker: Redis is not available.")
        logger.error("Please start Redis and try again.")
        logger.error("See REDIS_SETUP.md for instructions.")
        # Note: We can't exit here as the worker process is already starting
        # But the connection will fail with a clear error message


if __name__ == '__main__':
    # Check Redis connection before starting
    if not check_redis_connection():
        logger.error("Cannot start Celery worker: Redis is not available.")
        logger.error("Please start Redis and try again.")
        sys.exit(1)
    celery_app.start()

