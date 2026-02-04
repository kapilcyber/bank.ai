from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from src.middleware.auth_middleware import get_admin_user
from src.workers.tasks import process_outlook_resumes
from src.utils.logger import get_logger
import redis
from typing import Optional

logger = get_logger(__name__)
router = APIRouter(prefix="/api/resumes/outlook", tags=["Outlook Resume Sync"])

@router.post("/trigger")
async def trigger_outlook_sync(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_admin_user),
    max_emails: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of emails to process"),
    include_read: Optional[bool] = Query(False, description="Include read emails in processing"),
    require_keywords: Optional[bool] = Query(False, description="Only process emails with resume keywords in subject")
):
    """
    Manually trigger the Outlook resume sync pipeline.
    This tries to queue a Celery task, but falls back to FastAPI BackgroundTasks 
    if Redis is not available.
    
    Parameters:
    - max_emails: Maximum number of emails to process (default: 100, max: 1000)
    - include_read: If True, also process read emails (default: False)
    - require_keywords: If True, only process emails with resume keywords in subject (default: False)
    """
    try:
        logger.info(f"Outlook sync triggered by admin: {current_user['email']} (max_emails={max_emails}, include_read={include_read}, require_keywords={require_keywords})")
        
        try:
            # Attempt to trigger via Celery
            task = process_outlook_resumes.delay(max_emails=max_emails, include_read=include_read, require_keywords=require_keywords)
            return {
                "success": True,
                "message": "Outlook sync pipeline activated (via Celery)",
                "task_id": task.id,
                "parameters": {
                    "max_emails": max_emails,
                    "include_read": include_read,
                    "require_keywords": require_keywords
                }
            }
        except (redis.exceptions.ConnectionError, Exception) as e:
            logger.warning(f"Celery/Redis connection failed ({e}). Falling back to local BackgroundTask.")
            
            # Fallback: Run the function logic in a local background thread
            # We call the core logic function directly (it's defined in tasks.py)
            background_tasks.add_task(process_outlook_resumes, max_emails=max_emails, include_read=include_read, require_keywords=require_keywords)
            
            return {
                "success": True,
                "message": "Outlook sync pipeline activated (Local Fallback - Redis not found)",
                "fallback": True,
                "parameters": {
                    "max_emails": max_emails,
                    "include_read": include_read,
                    "require_keywords": require_keywords
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to trigger Outlook sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

