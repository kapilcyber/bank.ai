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
def process_outlook_resumes(max_emails: int = 100, include_read: bool = False, require_keywords: bool = False):
    """
    Fetch and process resumes from Outlook (Celery task).
    
    Args:
        max_emails: Maximum number of emails to process (default 100)
        include_read: If True, also process read emails (default False)
        require_keywords: If True, only process emails with resume keywords in subject (default False)
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
        
        async with AsyncSessionLocal() as db:
            outlook = OutlookService()
            try:
                emails = outlook.fetch_emails_to_process(max_emails=max_emails, include_read=include_read, require_keywords=require_keywords)
                logger.info(f"Found {len(emails)} Outlook emails to process (max_emails={max_emails}, include_read={include_read}, require_keywords={require_keywords})")
                
                for email in emails:
                    message_id = email.get("id")
                    try:
                        subject = email.get("subject", "No Subject")
                        sender_data = email.get("from", {}).get("emailAddress", {})
                        sender_email = sender_data.get("address", "unknown@outlook.com")
                        sender_name = sender_data.get("name", "Unknown")
                        
                        attachments = outlook.get_email_attachments(message_id)
                        for att in attachments:
                            att_id = att.get("id")  # Get attachment ID
                            att_name = att.get("name")
                            att_content = att.get("content")
                            att_ext = att.get("extension")
                            
                            # Create unique source_id per attachment: message_id + attachment_id
                            # This allows multiple resumes from the same email to be saved
                            attachment_source_id = f"{message_id}_{att_id}" if att_id else f"{message_id}_{att_name}_{int(datetime.utcnow().timestamp())}"
                            
                            # Save to storage using StorageService
                            file_obj = BytesIO(att_content)
                            upload_file = UploadFile(
                                filename=att_name,
                                file=file_obj,
                                size=len(att_content)
                            )
                            
                            # Get file content and mime type for database storage
                            file_path, _, file_content, mime_type = await StorageService.upload(upload_file, subfolder="resumes", save_to_db=False)
                            
                            # Parse resume
                            parsed_data = await parse_resume(file_path, att_ext)
                            
                            # Check if email already exists and modify it to make unique BEFORE saving
                            # This ensures ALL resumes are saved, even with duplicate emails
                            resume_email = parsed_data.get('resume_contact_info')
                            if resume_email and resume_email != "Not mentioned":
                                from sqlalchemy import func
                                query_by_email = select(Resume).where(
                                    func.lower(Resume.parsed_data['resume_contact_info'].astext) == resume_email.lower()
                                )
                                result_by_email = await db.execute(query_by_email)
                                existing_by_email = result_by_email.scalar_one_or_none()
                                
                                # If email exists, modify it to make it unique (add timestamp suffix)
                                if existing_by_email:
                                    timestamp_suffix = int(datetime.utcnow().timestamp() * 1000)  # Use milliseconds for better uniqueness
                                    unique_email = f"{resume_email}_{timestamp_suffix}"
                                    parsed_data['resume_contact_info'] = unique_email
                                    parsed_data['original_email'] = resume_email  # Keep original for reference
                                    logger.info(f"Email {resume_email} already exists. Using unique email: {unique_email} for attachment {att_name}")
                            
                            # Store in database - check by attachment-specific source_id
                            query = select(Resume).where(
                                Resume.source_type == 'outlook',
                                Resume.source_id == attachment_source_id
                            )
                            result = await db.execute(query)
                            existing_resume = result.scalar_one_or_none()
                            
                            source_metadata = {
                                'message_id': message_id,
                                'attachment_id': att_id,
                                'attachment_name': att_name,
                                'sender_email': sender_email,
                                'sender_name': sender_name,
                                'subject': subject,
                                'received_at': email.get('receivedDateTime')
                            }
                            
                            if existing_resume:
                                # Same attachment already processed - update it
                                existing_resume.filename = att_name
                                existing_resume.file_url = f"/api/resumes/{existing_resume.id}/file"  # Use API endpoint
                                existing_resume.file_content = file_content  # Store file in database
                                existing_resume.file_mime_type = mime_type
                                existing_resume.parsed_data = parsed_data
                                existing_resume.skills = parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', []))
                                existing_resume.experience_years = parsed_data.get('resume_experience', 0)
                                existing_resume.source_metadata = source_metadata
                                logger.info(f"Updated Outlook resume: {attachment_source_id}")
                            else:
                                # New attachment - create new resume (email already made unique if needed)
                                resume = Resume(
                                    filename=att_name,
                                    file_url=f"/api/resumes/0/file",  # Placeholder, will be updated after save
                                    source_type='outlook',
                                    source_id=attachment_source_id,  # Unique per attachment
                                    source_metadata=source_metadata,
                                    raw_text=parsed_data.get('raw_text', ''),
                                    parsed_data=parsed_data,  # This now has unique email if duplicate was detected
                                    file_content=file_content,  # Store file in database
                                    file_mime_type=mime_type,
                                    skills=parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', [])) or [],
                                    experience_years=parsed_data.get('resume_experience', 0),
                                    uploaded_by=sender_email,
                                    meta_data={
                                        'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                                        'outlook_metadata': source_metadata
                                    }
                                )
                                db.add(resume)
                                await db.flush()  # Flush to get the resume ID
                                resume.file_url = f"/api/resumes/{resume.id}/file"  # Update with actual ID
                                logger.info(f"Successfully processed Outlook resume attachment: {att_name} (source_id: {attachment_source_id}, resume_id: {resume.id})")
                        
                        # Mark as read in Outlook only after successful DB commit
                        await db.commit()
                        outlook.mark_processed(message_id)
                        logger.info(f"Successfully committed and marked as processed: {message_id}")
                    except Exception as e:
                        await db.rollback()
                        error_msg = str(e)
                        
                        # Check if it's a duplicate source_id (same attachment already processed)
                        if "uq_resume_source" in error_msg:
                            logger.warning(f"Resume for {attachment_source_id if 'attachment_source_id' in locals() else message_id} already exists (same attachment). Marking as processed.")
                            outlook.mark_processed(message_id)
                        # Check if it's a duplicate email - modify email and retry (shouldn't happen now, but as fallback)
                        elif "uq_resume_email_json" in error_msg or ("UniqueViolationError" in error_msg and "email" in error_msg.lower()):
                            logger.info(f"Resume email already exists (unexpected). Modifying email to make it unique and retrying.")
                            try:
                                # Modify the email in parsed_data to make it unique
                                if 'parsed_data' in locals() and parsed_data:
                                    original_email = parsed_data.get('resume_contact_info', '')
                                    if original_email and original_email != "Not mentioned":
                                        timestamp_suffix = int(datetime.utcnow().timestamp() * 1000)
                                        unique_email = f"{original_email}_{timestamp_suffix}"
                                        parsed_data['resume_contact_info'] = unique_email
                                        parsed_data['original_email'] = original_email
                                        logger.info(f"Modified email from {original_email} to {unique_email}")
                                
                                # Retry creating the resume with modified email
                                resume_retry = Resume(
                                    filename=att_name if 'att_name' in locals() else 'resume.pdf',
                                    file_url=f"/api/resumes/0/file",  # Placeholder, will be updated after save
                                    source_type='outlook',
                                    source_id=attachment_source_id if 'attachment_source_id' in locals() else f"{message_id}_{int(datetime.utcnow().timestamp())}",
                                    source_metadata=source_metadata if 'source_metadata' in locals() else {},
                                    raw_text=parsed_data.get('raw_text', '') if 'parsed_data' in locals() else '',
                                    parsed_data=parsed_data if 'parsed_data' in locals() else {},
                                    file_content=file_content if 'file_content' in locals() else None,  # Store file in database
                                    file_mime_type=mime_type if 'mime_type' in locals() else None,
                                    skills=parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', [])) or [] if 'parsed_data' in locals() else [],
                                    experience_years=parsed_data.get('resume_experience', 0) if 'parsed_data' in locals() else 0,
                                    uploaded_by=sender_email if 'sender_email' in locals() else 'unknown@outlook.com',
                                    meta_data={
                                        'parsing_method': parsed_data.get('parsing_method', 'unknown') if 'parsed_data' in locals() else 'unknown',
                                        'outlook_metadata': source_metadata if 'source_metadata' in locals() else {},
                                        'email_modified_for_uniqueness': True
                                    }
                                )
                                db.add(resume_retry)
                                await db.flush()  # Flush to get the resume ID
                                resume_retry.file_url = f"/api/resumes/{resume_retry.id}/file"  # Update with actual ID
                                await db.commit()
                                outlook.mark_processed(message_id)
                                logger.info(f"Successfully saved resume with modified email (source_id: {attachment_source_id if 'attachment_source_id' in locals() else message_id}, resume_id: {resume_retry.id})")
                            except Exception as retry_error:
                                await db.rollback()
                                logger.error(f"Failed to save resume with modified email: {retry_error}")
                                outlook.mark_processed(message_id)  # Mark as processed to avoid infinite loop
                        else:
                            logger.error(f"Error processing email {message_id}: {e}")
                            # Don't re-raise here so other emails can be processed

            except Exception as e:
                logger.error(f"Error processing Outlook resumes: {e}")
                raise

    asyncio.run(_process())
    return {"status": "success"}
