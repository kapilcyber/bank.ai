"""Admin-only routes for employee list config and CSV upload."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel
from typing import Optional, List

from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user
from src.models.employee_list import CompanyEmployeeList
from src.models.user_db import User
from src.services.employee_list_config import (
    get_employee_list_config,
    set_employee_list_config,
    replace_employee_list_from_csv,
    set_left_employees_after_upload,
    get_left_employees_after_upload,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin - Employee List"])


class EmployeeListConfigUpdate(BaseModel):
    enabled: Optional[bool] = None


class DowngradeLeftEmployeesBody(BaseModel):
    """User IDs to downgrade from Company Employee to Guest User (from left_employees after upload)."""
    user_ids: List[int]


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
    """Upload CSV or Excel (.xlsx, .xls) to replace company employee list (admin only). Columns: employee_id, full_name, email.
    Returns count, message, and left_employees: users who were in the previous list but not in the new list and are Company Employee (so admin can downgrade to Guest)."""
    from src.services.employee_list_config import ALLOWED_EXTENSIONS
    fn = (file.filename or "").lower()
    if not file.filename or not any(fn.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="File must be CSV or Excel (.csv, .xlsx, .xls)")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    try:
        count, removed = await replace_employee_list_from_csv(db, content, file.filename or "upload.csv")
        # Build list: everyone who left (in old list, not in new list). Add user_id only for platform Company Employees (for downgrade).
        left_employees: List[dict] = []
        removed_by_email = {r["email"]: r for r in removed} if removed else {}
        if removed:
            removed_emails = [r["email"] for r in removed if r["email"]]
            users_result = await db.execute(
                select(User).where(
                    func.lower(User.email).in_([e.lower() for e in removed_emails]),
                    User.employment_type == "Company Employee",
                )
            )
            user_by_email = {(u.email or "").strip().lower(): u for u in users_result.scalars().all()}
            for r in removed:
                email_lower = (r.get("email") or "").strip().lower()
                u = user_by_email.get(email_lower)
                left_employees.append({
                    "employee_id": (r.get("employee_id") or "").strip(),
                    "full_name": (r.get("full_name") or "").strip() or None,
                    "email": r.get("email") or "",
                    "user_id": u.id if u else None,
                })
        await set_left_employees_after_upload(db, left_employees)  # always save (updates after each upload)
        return {
            "count": count,
            "message": f"Updated {count} employees",
            "left_employees": left_employees,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/employee-list/left-after-upload")
async def get_left_after_upload(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get the list of employees who were in the previous list but not in the new one (difference after last upload). Admin only."""
    left = await get_left_employees_after_upload(db)
    return {"left_employees": left}


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


@router.post("/employee-list/downgrade-left")
async def downgrade_left_employees(
    body: DowngradeLeftEmployeesBody,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Set employment_type to 'Guest User' for given user IDs (only those who are Company Employee). Admin only."""
    if not body.user_ids:
        return {"updated": 0, "message": "No users to update"}
    result = await db.execute(
        update(User)
        .where(User.id.in_(body.user_ids), User.employment_type == "Company Employee")
        .values(employment_type="Guest User")
    )
    await db.commit()
    n = result.rowcount
    return {"updated": n, "message": f"Updated {n} user(s) to Guest User"}
