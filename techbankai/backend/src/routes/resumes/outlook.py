from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from src.middleware.auth_middleware import get_admin_user
from src.workers.tasks import process_outlook_resumes
from src.utils.logger import get_logger
import redis

logger = get_logger(__name__)
router = APIRouter(prefix="/api/resumes/outlook", tags=["Outlook Resume Sync"])

@router.post("/trigger")
async def trigger_outlook_sync(background_tasks: BackgroundTasks, current_user: dict = Depends(get_admin_user)):
    """
    Manually trigger the Outlook resume sync pipeline.
    This tries to queue a Celery task, but falls back to FastAPI BackgroundTasks 
    if Redis is not available.
    """
    try:
        logger.info(f"Outlook sync triggered by admin: {current_user['email']}")
        
        try:
            # Attempt to trigger via Celery
            task = process_outlook_resumes.delay()
            return {
                "success": True,
                "message": "Outlook sync pipeline activated (via Celery)",
                "task_id": task.id
            }
        except (redis.exceptions.ConnectionError, Exception) as e:
            logger.warning(f"Celery/Redis connection failed ({e}). Falling back to local BackgroundTask.")
            
            # Fallback: Run the function logic in a local background thread
            # We call the core logic function directly (it's defined in tasks.py)
            background_tasks.add_task(process_outlook_resumes)
            
            return {
                "success": True,
                "message": "Outlook sync pipeline activated (Local Fallback - Redis not found)",
                "fallback": True
            }
            
    except Exception as e:
        logger.error(f"Failed to trigger Outlook sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

