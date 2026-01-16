"""User profile API routes (view & update current user profile)."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
import os
import uuid
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_current_user
from src.models.user_db import User
from src.models.user import UserResponse
from src.utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/api/user", tags=["User Profile"])

# Ensure profile uploads directory exists
UPLOAD_DIR = "uploads/profiles"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class UserProfileUpdate(BaseModel):
    """Fields that a user is allowed to update on their profile."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    dob: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    employment_type: Optional[str] = None


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get the current authenticated user's profile."""
    try:
        query = select(User).where(User.email == current_user["email"])
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            mode=user.mode or "user",
            employment_type=user.employment_type,
            employee_id=user.employee_id,
            freelancer_id=user.freelancer_id,
            profile_img=user.profile_img,
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Update the current authenticated user's profile."""
    try:
        query = select(User).where(User.email == current_user["email"])
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Apply updates only for provided fields
        if profile_update.name is not None:
            user.name = profile_update.name
        if profile_update.dob is not None:
            user.dob = profile_update.dob
        if profile_update.state is not None:
            user.state = profile_update.state
        if profile_update.city is not None:
            user.city = profile_update.city
        if profile_update.pincode is not None:
            user.pincode = profile_update.pincode
        if profile_update.employment_type is not None:
            user.employment_type = profile_update.employment_type

        await db.commit()
        await db.refresh(user)

        logger.info(f"Updated profile for user: {user.email}")

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            mode=user.mode or "user",
            employment_type=user.employment_type,
            employee_id=user.employee_id,
            freelancer_id=user.freelancer_id,
            profile_img=user.profile_img,
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profile-photo", response_model=UserResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Upload or update the user's profile photo."""
    try:
        query = select(User).where(User.email == current_user["email"])
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        filename = f"profile_{user.id}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Save the file
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        # Update user record with the URL
        user.profile_img = f"/uploads/profiles/{filename}"
        await db.commit()
        await db.refresh(user)

        logger.info(f"Updated profile photo for user: {user.email}")

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            mode=user.mode or "user",
            profile_img=user.profile_img,
            created_at=user.created_at,
        )
    except Exception as e:
        logger.error(f"Profile photo upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload profile photo")


@router.delete("/profile-photo", response_model=UserResponse)
async def delete_profile_photo(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Delete the user's profile photo."""
    try:
        query = select(User).where(User.email == current_user["email"])
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete the file from disk if it exists
        if user.profile_img:
            # Extract filename from URL path
            filename = user.profile_img.split("/")[-1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted profile photo file: {filepath}")

        # Clear the profile_img field
        user.profile_img = None
        await db.commit()
        await db.refresh(user)

        logger.info(f"Removed profile photo for user: {user.email}")

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            mode=user.mode or "user",
            profile_img=user.profile_img,
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile photo delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete profile photo")


