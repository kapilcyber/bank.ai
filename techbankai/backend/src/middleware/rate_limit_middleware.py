"""Rate limiting middleware using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from starlette.responses import JSONResponse
import redis

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize limiter
# Use Redis if available, otherwise use in-memory storage
storage_uri = "memory://"
if settings.celery_broker_url and settings.celery_broker_url.startswith("redis://"):
    try:
        # Test Redis connection
        redis_url = settings.celery_broker_url
        # Extract host and port from redis://host:port/db
        parts = redis_url.replace("redis://", "").split("/")
        host_port = parts[0].split(":")
        host = host_port[0] if len(host_port) > 0 else "localhost"
        port = int(host_port[1]) if len(host_port) > 1 else 6379
        
        # Try to connect to Redis
        r = redis.Redis(host=host, port=port, socket_connect_timeout=2, decode_responses=True)
        r.ping()
        storage_uri = redis_url
        logger.info(f"✅ Rate limiter using Redis: {host}:{port}")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available ({e}), using in-memory storage for rate limiting")
        storage_uri = "memory://"
else:
    logger.info("ℹ️ Using in-memory storage for rate limiting")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default limit for API endpoints
    storage_uri=storage_uri,
    headers_enabled=True
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler."""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)} on {request.url.path}")
    return JSONResponse(
        status_code=429,
        content={
            "error": True,
            "message": "Rate limit exceeded. Please try again later.",
            "detail": f"Rate limit: {exc.detail}"
        },
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"}
    )

