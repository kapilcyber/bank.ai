"""Admin-only routes for employee list config and CSV upload."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user
from src.models.employee_list import CompanyEmployeeList
from src.services.employee_list_config import (
    get_employee_list_config,
    set_employee_list_config,
    replace_employee_list_from_csv,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin - Employee List"])


class EmployeeListConfigUpdate(BaseModel):
    enabled: Optional[bool] = None


@router.get("/employee-list/config")
async def get_config(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get employee list config: enabled, count (from uploaded list in DB)."""
    config = await get_employee_list_config(db)
    return config


@router.put("/employee-list/config")
async def update_config(
    body: EmployeeListConfigUpdate,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Update employee list config (admin only). Only verification on/off is updated."""
    await set_employee_list_config(db, enabled=body.enabled)
    return await get_employee_list_config(db)


@router.post("/employee-list/upload")
async def upload_csv(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db),
    file: UploadFile = File(...),
):
    """Upload CSV or Excel (.xlsx, .xls) to replace company employee list (admin only). Columns: employee_id, full_name, email."""
    from src.services.employee_list_config import ALLOWED_EXTENSIONS
    fn = (file.filename or "").lower()
    if not file.filename or not any(fn.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="File must be CSV or Excel (.csv, .xlsx, .xls)")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    try:
        count = await replace_employee_list_from_csv(db, content, file.filename or "upload.csv")
        return {"count": count, "message": f"Updated {count} employees"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/employee-list")
async def list_employees(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    """List uploaded company employees (admin only). Only populated when source is uploaded."""
    result = await db.execute(
        select(CompanyEmployeeList)
        .order_by(CompanyEmployeeList.employee_id)
        .limit(limit)
        .offset(offset)
    )
    rows = result.scalars().all()
    return {
        "items": [
            {"employee_id": r.employee_id, "full_name": r.full_name, "email": r.email}
            for r in rows
        ],
        "total": len(rows),
    }
