"""Celery tasks for background processing."""
from src.workers.celery_app import celery_app
from src.services.resume_parser import parse_resume
from src.services.storage import StorageService
from src.models.resume import Resume
from src.config.database import AsyncSessionLocal
from sqlalchemy import select
from src.utils.logger import get_logger
import base64
import tempfile
import os

logger = get_logger(__name__)


@celery_app.task(name="src.workers.tasks.process_gmail_resume")
def process_gmail_resume(message_id: str, attachment_data: bytes, sender: str = None, subject: str = None):
    """
    Process Gmail resume attachment (Celery task).
    This runs asynchronously in the background.
    """
    import asyncio
    
    async def _process():
        from src.config.database import engine
        await engine.dispose()  # Critical for Windows: Clear stale connections
        
        db = AsyncSessionLocal()
        try:
            # Decode attachment if base64 encoded
            if isinstance(attachment_data, str):
                try:
                    attachment_bytes = base64.b64decode(attachment_data)
                except Exception:
                    attachment_bytes = attachment_data.encode() if isinstance(attachment_data, str) else attachment_data
            else:
                attachment_bytes = attachment_data
            
            # Save attachment to temporary file
            file_extension = 'pdf'  # Default, could be determined from attachment metadata
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                tmp_file.write(attachment_bytes)
                tmp_file_path = tmp_file.name
            
            try:
                # Parse resume
                logger.info(f"Processing Gmail resume: message_id={message_id}")
                parsed_data = await parse_resume(tmp_file_path, file_extension)
                
                # Determine file URL (upload to storage)
                # For now, save locally; later integrate with Google Drive
                from fastapi import UploadFile
                from io import BytesIO
                
                # Create a file-like object for storage service
                file_obj = BytesIO(attachment_bytes)
                file_obj.name = f"{message_id}.{file_extension}"
                
                # Upload to storage (Google Drive or local)
                # Note: This is a simplified version; in production, you'd use proper async file handling
                file_url = f"/uploads/resumes/{message_id}.{file_extension}"
                
                # Check if resume with this message_id already exists
                query = select(Resume).where(
                    Resume.source_type == 'gmail',
                    Resume.source_id == message_id
                )
                result = await db.execute(query)
                existing_resume = result.scalar_one_or_none()
                
                if existing_resume:
                    # Update existing record
                    existing_resume.filename = f"{message_id}.{file_extension}"
                    existing_resume.file_url = file_url
                    existing_resume.parsed_data = parsed_data
                    existing_resume.skills = parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', []))
                    existing_resume.experience_years = parsed_data.get('resume_experience', 0)
                    existing_resume.source_metadata = {
                        'message_id': message_id,
                        'sender': sender,
                        'subject': subject
                    }
                    await db.commit()
                    await db.refresh(existing_resume)
                    logger.info(f"Updated Gmail resume: {message_id}")
                else:
                    # Create new record
                    resume = Resume(
                        filename=f"{message_id}.{file_extension}",
                        file_url=file_url,
                        source_type='gmail',
                        source_id=message_id,
                        source_metadata={
                            'message_id': message_id,
                            'sender': sender,
                            'subject': subject
                        },
                        raw_text=parsed_data.get('raw_text', ''),
                        parsed_data=parsed_data,
                        skills=parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', [])),
                        experience_years=parsed_data.get('resume_experience', 0),
                        uploaded_by=sender or 'gmail@unknown.com',
                        meta_data={
                            'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                            'gmail_metadata': {
                                'sender': sender,
                                'subject': subject
                            }
                        }
                    )
                    
                    db.add(resume)
                    await db.commit()
                    await db.refresh(resume)
                    logger.info(f"Successfully processed Gmail resume: {message_id}")
            
            except Exception as e:
                await db.rollback()
                error_msg = str(e)
                if "UniqueViolationError" in error_msg or "uq_resume_email_json" in error_msg:
                    logger.warning(f"Gmail resume {message_id} is a duplicate. Skipping.")
                else:
                    logger.error(f"Failed to process Gmail resume {message_id}: {e}")
                    raise
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        
        except Exception as e:
            logger.error(f"Error in Gmail task loop {message_id}: {e}")
            raise
        finally:
            await db.close()
    
    # Run async function
    asyncio.run(_process())
    return {"status": "success", "message_id": message_id}


@celery_app.task(name="src.workers.tasks.process_outlook_resumes")
def process_outlook_resumes():
    """
    Fetch and process resumes from Outlook (Celery task).
    """
    import asyncio
    from src.services.outlook_service import OutlookService
    from src.services.storage import StorageService
    from fastapi import UploadFile
    from io import BytesIO
    from datetime import datetime

    async def _process():
        from src.config.database import engine
        await engine.dispose()  # Critical for Windows: Clear stale connections
        
        db = AsyncSessionLocal()
        outlook = OutlookService()
        try:
            emails = outlook.fetch_emails_to_process()
            logger.info(f"Found {len(emails)} Outlook emails to process")
            
            for email in emails:
                message_id = email.get("id")
                try:
                    subject = email.get("subject", "No Subject")
                    sender_data = email.get("from", {}).get("emailAddress", {})
                    sender_email = sender_data.get("address", "unknown@outlook.com")
                    sender_name = sender_data.get("name", "Unknown")
                    
                    attachments = outlook.get_email_attachments(message_id)
                    for att in attachments:
                        att_name = att.get("name")
                        att_content = att.get("content")
                        att_ext = att.get("extension")
                        
                        # Save to storage using StorageService
                        file_obj = BytesIO(att_content)
                        upload_file = UploadFile(
                            filename=att_name,
                            file=file_obj,
                            size=len(att_content)
                        )
                        
                        file_path, file_url = await StorageService.upload(upload_file, subfolder="resumes")
                        
                        # Parse resume
                        parsed_data = await parse_resume(file_path, att_ext)
                        
                        # Store in database
                        query = select(Resume).where(
                            Resume.source_type == 'outlook',
                            Resume.source_id == message_id
                        )
                        result = await db.execute(query)
                        existing_resume = result.scalar_one_or_none()
                        
                        source_metadata = {
                            'message_id': message_id,
                            'sender_email': sender_email,
                            'sender_name': sender_name,
                            'subject': subject,
                            'received_at': email.get('receivedDateTime')
                        }
                        
                        if existing_resume:
                            existing_resume.filename = att_name
                            existing_resume.file_url = file_url
                            existing_resume.parsed_data = parsed_data
                            existing_resume.skills = parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', []))
                            existing_resume.experience_years = parsed_data.get('resume_experience', 0)
                            existing_resume.source_metadata = source_metadata
                            logger.info(f"Updated Outlook resume: {message_id}")
                        else:
                            resume = Resume(
                                filename=att_name,
                                file_url=file_url,
                                source_type='outlook',
                                source_id=message_id,
                                source_metadata=source_metadata,
                                raw_text=parsed_data.get('raw_text', ''),
                                parsed_data=parsed_data,
                                skills=parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', [])) or [],
                                experience_years=parsed_data.get('resume_experience', 0),
                                uploaded_by=sender_email,
                                meta_data={
                                    'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                                    'outlook_metadata': source_metadata
                                }
                            )
                            db.add(resume)
                            logger.info(f"Successfully processed Outlook resume: {message_id}")
                    
                    # Mark as read in Outlook only after successful DB commit
                    await db.commit()
                    outlook.mark_processed(message_id)
                    logger.info(f"Successfully committed and marked as processed: {message_id}")
                except Exception as e:
                    await db.rollback()
                    error_msg = str(e)
                    if "UniqueViolationError" in error_msg or "uq_resume_email_json" in error_msg:
                        logger.warning(f"Resume for {message_id} is a duplicate (email already exists). Marking as processed to avoid loop.")
                        outlook.mark_processed(message_id)
                    else:
                        logger.error(f"Error processing email {message_id}: {e}")
                        # Don't re-raise here so other emails can be processed

        except Exception as e:
            logger.error(f"Error processing Outlook resumes: {e}")
            raise
        finally:
            await db.close()

    asyncio.run(_process())
    return {"status": "success"}
