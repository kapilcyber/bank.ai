"""Start Celery worker with Redis connection check."""
import sys
import subprocess
from src.workers.celery_app import check_redis_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Start Celery worker after checking Redis connection."""
    logger.info("Checking Redis connection before starting Celery worker...")
    
    if not check_redis_connection():
        logger.error("Cannot start Celery worker: Redis is not available.")
        logger.error("Please start Redis and try again.")
        sys.exit(1)
    
    logger.info("Redis connection successful. Starting Celery worker...")
    
    # Start the worker using Celery command
    # This is equivalent to: celery -A src.workers.celery_app worker --loglevel=info --pool=solo
    try:
        subprocess.run([
            sys.executable, '-m', 'celery',
            '-A', 'src.workers.celery_app',
            'worker',
            '--loglevel=info',
            '--pool=solo',  # Use solo pool for Windows compatibility
        ], check=True)
    except KeyboardInterrupt:
        logger.info("Celery worker stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"Celery worker exited with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

