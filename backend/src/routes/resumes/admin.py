from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import uuid
from src.models.resume import Resume
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user
from src.services.storage import save_uploaded_file
from src.services.resume_parser import parse_resume
from src.utils.validators import validate_file_type
from src.utils.logger import get_logger
from src.utils.user_type_mapper import get_user_type_from_source_type
from src.utils.resume_processor import save_structured_resume_data

logger = get_logger(__name__)
router = APIRouter(prefix="/api/resumes/admin", tags=["Admin Resume Uploads"])

ALLOWED_EXTENSIONS = ['pdf', 'docx']

def clean_null_bytes(text: str) -> str:
    """Remove null bytes from text to prevent PostgreSQL errors"""
    if text is None:
        return ""
    if isinstance(text, str):
        return text.replace('\x00', '').replace('\0', '')
    return str(text).replace('\x00', '').replace('\0', '')

def clean_dict_values(data: dict) -> dict:
    """Recursively clean null bytes from dictionary values"""
    if not isinstance(data, dict):
        return data
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned[key] = clean_null_bytes(value)
        elif isinstance(value, dict):
            cleaned[key] = clean_dict_values(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_null_bytes(str(v)) if isinstance(v, str) else v for v in value]
        else:
            cleaned[key] = value
    return cleaned

@router.post("/bulk")
async def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Bulk upload multiple resume files (Admin only)
    Processes files safely, uploads to Google Drive (if configured), and stores in database
    """
    try:
        uploaded_resumes = []
        errors = []
        
        for file in files:
            try:
                # Validate file type
                if not validate_file_type(file.filename, ALLOWED_EXTENSIONS):
                    errors.append(f"{file.filename}: Invalid file type. Only PDF and DOCX allowed.")
                    continue
                
                # Save file to database (returns file_content and mime_type)
                file_id, file_url, file_content, mime_type = await save_uploaded_file(file, subfolder="resumes", save_to_db=True)
                file_extension = file.filename.split('.')[-1]
                
                # Save file temporarily for parsing (parser needs file path)
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                    tmp_file.write(file_content)
                    file_path = tmp_file.name
                
                try:
                    # Parse resume
                    logger.info(f"Parsing resume: {file.filename}")
                    parsed_data = await parse_resume(file_path, file_extension)
                    
                    # Clean null bytes from parsed data
                    parsed_data = clean_dict_values(parsed_data)
                    
                    # Generate unique source_id for admin uploads to avoid unique constraint violation
                    admin_source_id = f"admin_{uuid.uuid4().hex[:16]}_{int(datetime.utcnow().timestamp() * 1000)}"
                    
                    # Create resume record with file_content
                    resume = Resume(
                        filename=file.filename,
                        file_url=file_url,  # Will be updated with actual resume_id after save
                        file_content=file_content,  # Store file in database
                        file_mime_type=mime_type,
                        source_type='admin',
                        source_id=admin_source_id,
                        raw_text=clean_null_bytes(parsed_data.get('raw_text', '')),
                        parsed_data=parsed_data,
                        skills=parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', [])),
                        experience_years=parsed_data.get('resume_experience', 0),
                        uploaded_by=current_user['email'],
                        meta_data={
                            'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                            'file_size': len(file_content),
                            'user_type': get_user_type_from_source_type('admin')  # Always set normalized user_type
                        }
                    )
                    
                    db.add(resume)
                    await db.commit()
                    await db.refresh(resume)
                    
                    # Update file_url with actual resume_id
                    resume.file_url = f"/api/resumes/{resume.id}/file"
                    await db.commit()
                    
                    # Save structured child records (Experience, Certifications)
                    await save_structured_resume_data(db, resume.id, parsed_data)
                    await db.commit()
                finally:
                    # Clean up temporary file
                    if os.path.exists(file_path):
                        try:
                            os.unlink(file_path)
                        except:
                            pass
                
                uploaded_resumes.append({
                    'id': resume.id,
                    'filename': resume.filename,
                    'candidate_name': parsed_data.get('resume_candidate_name', 'Unknown'),
                    'skills': resume.skills,
                    'experience_years': resume.experience_years
                })
                
                logger.info(f"Successfully uploaded resume: {file.filename}")
            
            except Exception as e:
                logger.error(f"Failed to process {file.filename}: {e}")
                errors.append(f"{file.filename}: {str(e)}")
        
        return {
            'success': len(uploaded_resumes),
            'failed': len(errors),
            'uploaded_resumes': uploaded_resumes,
            'errors': errors
        }
    
    except Exception as e:
        logger.error(f"Bulk upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

