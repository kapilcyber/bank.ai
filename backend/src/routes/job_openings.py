"""Job Openings API routes."""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
import uuid
from datetime import datetime

from sqlalchemy.orm import selectinload

from src.models.job_opening import JobOpening
from src.models.job_application import JobApplication
from src.models.resume import Resume
from src.config.database import get_postgres_db
from src.utils.response_formatter import format_resume_response
from src.middleware.auth_middleware import get_admin_user, get_current_user
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer(auto_error=False)
from src.services.storage import save_uploaded_file
from src.services.file_processor import extract_text_from_file
from src.utils.validators import validate_file_type
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/job-openings", tags=["Job Openings"])

ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc']


JOB_TYPES = ("internship", "full_time", "remote", "hybrid", "contract")


@router.post("")
async def create_job_opening(
    title: str = Form(...),
    location: str = Form(...),
    business_area: str = Form(...),
    experience_required: Optional[str] = Form(None),
    job_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    status: str = Form("active"),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Create a new job opening (admin only)."""
    try:
        # Validate status
        if status not in ["active", "inactive"]:
            raise HTTPException(status_code=400, detail="Status must be 'active' or 'inactive'")
        if job_type and job_type not in JOB_TYPES:
            raise HTTPException(status_code=400, detail="job_type must be one of: internship, full_time, remote, hybrid, contract")
        
        # Generate unique job_id
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        
        # Handle JD file upload if provided
        jd_file_url = None
        if jd_file:
            if not validate_file_type(jd_file.filename, ALLOWED_EXTENSIONS):
                raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, DOCX allowed.")
            
            file_path, file_url, _, _ = await save_uploaded_file(jd_file, subfolder="jd", save_to_db=False)
            jd_file_url = file_url
            
            # If description is not provided, try to extract from JD file
            if not description:
                try:
                    file_extension = jd_file.filename.split('.')[-1]
                    extracted_text = extract_text_from_file(file_path, file_extension)
                    if extracted_text:
                        description = extracted_text[:5000]  # Limit description length
                except Exception as e:
                    logger.warning(f"Failed to extract text from JD file: {e}")
        
        # Create job opening
        job_opening = JobOpening(
            job_id=job_id,
            title=title,
            location=location,
            business_area=business_area,
            experience_required=experience_required,
            job_type=job_type,
            description=description or "",
            jd_file_url=jd_file_url,
            status=status,
            created_by=current_user.get("email", "unknown")
        )
        
        db.add(job_opening)
        await db.commit()
        await db.refresh(job_opening)
        
        logger.info(f"Created job opening: {job_id} by {current_user.get('email')}")
        
        return {
            "id": job_opening.id,
            "job_id": job_opening.job_id,
            "title": job_opening.title,
            "location": job_opening.location,
            "business_area": job_opening.business_area,
            "experience_required": job_opening.experience_required,
            "job_type": job_opening.job_type,
            "description": job_opening.description,
            "jd_file_url": job_opening.jd_file_url,
            "status": job_opening.status,
            "created_at": job_opening.created_at.isoformat() if job_opening.created_at else None,
            "created_by": job_opening.created_by,
            "updated_at": job_opening.updated_at.isoformat() if job_opening.updated_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create job opening error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_job_openings(
    status: Optional[str] = Query(None, description="Filter by status: 'active', 'inactive', or 'all' (admin only)"),
    business_area: Optional[str] = Query(None, description="Filter by business area"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_postgres_db)
):
    """List all job openings. Public endpoint defaults to active only. Admins can see all."""
    try:
        query = select(JobOpening)
        is_admin = False
        
        # Try to get current user and check if admin (optional - won't fail if not authenticated)
        try:
            if credentials:
                current_user = await get_current_user(credentials, db)
                from src.middleware.auth_middleware import is_admin_mode
                is_admin = is_admin_mode(current_user.get("mode", ""))
        except:
            pass  # Not authenticated or not admin, continue as public user
        
        # Apply filters
        if status:
            if status == "all":
                if not is_admin:
                    raise HTTPException(status_code=403, detail="Admin access required to view all jobs")
                # Admin can see all jobs - don't filter by status
                pass
            elif status in ["active", "inactive"]:
                query = query.where(JobOpening.status == status)
            else:
                raise HTTPException(status_code=400, detail="Status must be 'active', 'inactive', or 'all' (admin only)")
        else:
            # Default to active jobs only for public access, all for admin
            if not is_admin:
                query = query.where(JobOpening.status == "active")
        
        if business_area:
            query = query.where(JobOpening.business_area == business_area)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(JobOpening.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        job_openings = result.scalars().all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "jobs": [
                {
                    "id": job.id,
                    "job_id": job.job_id,
                    "title": job.title,
                    "location": job.location,
                    "business_area": job.business_area,
                    "experience_required": job.experience_required,
                    "job_type": getattr(job, "job_type", None),
                    "description": job.description,
                    "jd_file_url": job.jd_file_url,
                    "status": job.status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "created_by": job.created_by,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
                for job in job_openings
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List job openings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filter")
async def filter_job_openings(
    business_area: Optional[str] = Query(None, description="Filter by business area"),
    title: Optional[str] = Query(None, description="Filter by job title (partial match)"),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Filter job openings by business_area or title (public endpoint)."""
    try:
        query = select(JobOpening).where(JobOpening.status == "active")
        
        if business_area:
            query = query.where(JobOpening.business_area == business_area)
        
        if title:
            query = query.where(JobOpening.title.ilike(f"%{title}%"))
        
        query = query.order_by(JobOpening.created_at.desc())
        result = await db.execute(query)
        job_openings = result.scalars().all()
        
        return {
            "total": len(job_openings),
            "jobs": [
                {
                    "id": job.id,
                    "job_id": job.job_id,
                    "title": job.title,
                    "location": job.location,
                    "business_area": job.business_area,
                    "experience_required": job.experience_required,
                    "job_type": getattr(job, "job_type", None),
                    "description": job.description,
                    "jd_file_url": job.jd_file_url,
                    "status": job.status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "created_by": job.created_by,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
                for job in job_openings
            ]
        }
    
    except Exception as e:
        logger.error(f"Filter job openings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/applicants/count")
async def get_job_applicant_count(
    job_id: str,
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get the number of applicants for a specific job (public endpoint)."""
    try:
        # Verify job exists
        job_result = await db.execute(select(JobOpening).where(JobOpening.job_id == job_id))
        if not job_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Job opening not found")
        count_result = await db.execute(
            select(func.count(JobApplication.id)).where(JobApplication.job_id == job_id)
        )
        count = count_result.scalar() or 0
        return {"job_id": job_id, "applicant_count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job applicant count error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/applicants")
async def get_job_applicants(
    job_id: str,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """List all applicants (resumes) for a specific job opening. Admin only. Same record shape as Records page."""
    try:
        job_result = await db.execute(select(JobOpening).where(JobOpening.job_id == job_id))
        job_opening = job_result.scalar_one_or_none()
        if not job_opening:
            raise HTTPException(status_code=404, detail="Job opening not found")

        app_result = await db.execute(
            select(JobApplication.resume_id, JobApplication.job_title, JobApplication.applied_at).where(JobApplication.job_id == job_id)
        )
        app_rows = app_result.all()
        if not app_rows:
            return {
                "job_id": job_id,
                "job_title": job_opening.title,
                "applicants": []
            }
        resume_ids = [row[0] for row in app_rows]
        # Map resume_id -> stored job title and applied_at (for this application)
        application_meta = {row[0]: {"job_title": row[1], "applied_at": row[2]} for row in app_rows}

        resumes_query = select(Resume).where(Resume.id.in_(resume_ids)).options(
            selectinload(Resume.work_history),
            selectinload(Resume.certificates),
            selectinload(Resume.educations)
        )
        res_result = await db.execute(resumes_query)
        resumes = res_result.scalars().all()
        applicants = []
        for r in resumes:
            try:
                data = format_resume_response(r)
                meta = application_meta.get(r.id, {})
                data["applied_for_job_title"] = meta.get("job_title") or job_opening.title
                data["applied_at"] = meta.get("applied_at").isoformat() if meta.get("applied_at") else None
                applicants.append(data)
            except Exception as resume_error:
                logger.warning(f"Failed to format applicant resume {r.id}: {resume_error}")
        return {
            "job_id": job_id,
            "job_title": job_opening.title,
            "applicants": applicants
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job applicants error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job_opening(
    job_id: str,
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get a specific job opening by job_id (public endpoint)."""
    try:
        query = select(JobOpening).where(JobOpening.job_id == job_id)
        result = await db.execute(query)
        job_opening = result.scalar_one_or_none()
        
        if not job_opening:
            raise HTTPException(status_code=404, detail="Job opening not found")
        
        return {
            "id": job_opening.id,
            "job_id": job_opening.job_id,
            "title": job_opening.title,
            "location": job_opening.location,
            "business_area": job_opening.business_area,
            "experience_required": job_opening.experience_required,
            "job_type": job_opening.job_type,
            "description": job_opening.description,
            "jd_file_url": job_opening.jd_file_url,
            "status": job_opening.status,
            "created_at": job_opening.created_at.isoformat() if job_opening.created_at else None,
            "created_by": job_opening.created_by,
            "updated_at": job_opening.updated_at.isoformat() if job_opening.updated_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job opening error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{job_id}")
async def update_job_opening(
    job_id: str,
    title: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    business_area: Optional[str] = Form(None),
    experience_required: Optional[str] = Form(None),
    job_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    status: Optional[str] = Form(None),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Update a job opening (admin only)."""
    try:
        query = select(JobOpening).where(JobOpening.job_id == job_id)
        result = await db.execute(query)
        job_opening = result.scalar_one_or_none()
        
        if not job_opening:
            raise HTTPException(status_code=404, detail="Job opening not found")
        
        # Update fields if provided
        if title is not None:
            job_opening.title = title
        if location is not None:
            job_opening.location = location
        if business_area is not None:
            job_opening.business_area = business_area
        if experience_required is not None:
            job_opening.experience_required = experience_required
        if job_type is not None:
            if job_type and job_type not in JOB_TYPES:
                raise HTTPException(status_code=400, detail="job_type must be one of: internship, full_time, remote, hybrid, contract")
            job_opening.job_type = job_type or None
        if description is not None:
            job_opening.description = description
        if status is not None:
            if status not in ["active", "inactive"]:
                raise HTTPException(status_code=400, detail="Status must be 'active' or 'inactive'")
            job_opening.status = status
        
        # Handle JD file upload if provided
        if jd_file:
            if not validate_file_type(jd_file.filename, ALLOWED_EXTENSIONS):
                raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, DOCX allowed.")
            
            file_path, file_url, _, _ = await save_uploaded_file(jd_file, subfolder="jd", save_to_db=False)
            job_opening.jd_file_url = file_url
            
            # If description is not provided, try to extract from JD file
            if not description:
                try:
                    file_extension = jd_file.filename.split('.')[-1]
                    extracted_text = extract_text_from_file(file_path, file_extension)
                    if extracted_text:
                        job_opening.description = extracted_text[:5000]
                except Exception as e:
                    logger.warning(f"Failed to extract text from JD file: {e}")
        
        job_opening.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(job_opening)
        
        logger.info(f"Updated job opening: {job_id} by {current_user.get('email')}")
        
        return {
            "id": job_opening.id,
            "job_id": job_opening.job_id,
            "title": job_opening.title,
            "location": job_opening.location,
            "business_area": job_opening.business_area,
            "experience_required": job_opening.experience_required,
            "job_type": job_opening.job_type,
            "description": job_opening.description,
            "jd_file_url": job_opening.jd_file_url,
            "status": job_opening.status,
            "created_at": job_opening.created_at.isoformat() if job_opening.created_at else None,
            "created_by": job_opening.created_by,
            "updated_at": job_opening.updated_at.isoformat() if job_opening.updated_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update job opening error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job_opening(
    job_id: str,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Delete a job opening (admin only)."""
    try:
        query = select(JobOpening).where(JobOpening.job_id == job_id)
        result = await db.execute(query)
        job_opening = result.scalar_one_or_none()
        
        if not job_opening:
            raise HTTPException(status_code=404, detail="Job opening not found")
        
        await db.execute(delete(JobOpening).where(JobOpening.job_id == job_id))
        await db.commit()
        
        logger.info(f"Deleted job opening: {job_id} by {current_user.get('email')}")
        
        return {"message": "Job opening deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete job opening error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

