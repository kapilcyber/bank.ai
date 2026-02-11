from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Dict
from starlette.responses import Response

from src.models.user import UserCreate, UserLogin, UserResponse
from src.models.user_db import User
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import create_access_token, get_current_user, blacklist_token, decode_access_token
from src.utils.logger import get_logger
from src.services.employee_list_config import (
    verify_employee_against_list,
    get_employee_list_config,
    is_employee_list_available,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class ForgotPasswordRequest(BaseModel):
    """Request to send a password reset code."""
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    """Request to verify a password reset code."""
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    """Request to reset password using a verification code."""
    email: EmailStr
    code: str
    new_password: str


class VerifyEmployeeRequest(BaseModel):
    """Request to verify employee ID and email against company CSV (no auth)."""
    employee_id: str
    email: str


class AdminSignupRequest(BaseModel):
    """Admin/staff signup - Admin, Talent Acquisition, HR."""
    name: str
    email: EmailStr
    password: str
    role: str  # Admin, Talent Acquisition, HR
    employee_id: str  # Required for all admin roles


_reset_tokens: Dict[str, Dict[str, datetime]] = {}

# Roles that get admin dashboard access
ADMIN_ROLES = {'admin', 'talent_acquisition', 'talent acquisition', 'hr'}


def is_admin_role(mode: str) -> bool:
    """Check if user mode grants admin dashboard access."""
    if not mode:
        return False
    return mode.strip().lower() in ADMIN_ROLES or 'admin' in mode.lower()


def _generate_reset_code() -> str:
    """Generate a 6-digit numeric reset code."""
    import secrets
    return f"{secrets.randbelow(10**6):06d}"

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_postgres_db)):
    """Register a new user with role verification"""
    import csv
    import os
    
    try:
        # Check if user already exists
        query = select(User).where(User.email == user.email.lower())
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=409, detail="User with this email already exists")
            
        # Role-based Logic
        freelancer_id = None
        employee_id = None
        
        # 1. Company Employee Verification (uses admin toggle and uploaded/static list)
        if user.employment_type == "Company Employee":
            if not user.employee_id:
                raise HTTPException(status_code=400, detail="Employee ID is required for Company Employees")
            config = await get_employee_list_config(db)
            if config.get("enabled", True) and not await is_employee_list_available(db):
                raise HTTPException(
                    status_code=503,
                    detail="Company employee list is not available. Please contact your administrator."
                )
            result = await verify_employee_against_list(user.employee_id, user.email, db)
            if config.get("enabled", True) and result is None:
                raise HTTPException(
                    status_code=403,
                    detail="Verification failed: Employee ID and Email do not match company records"
                )
            employee_id = user.employee_id.strip().upper()

        # 2. Freelancer ID Generation
        elif user.employment_type == "Freelancer":
            try:
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                freelancers_csv = os.path.join(root_dir, "Freelancers.csv")
                
                # Ensure file exists with header
                file_exists = os.path.isfile(freelancers_csv)
                
                # Determine next ID
                next_id_num = 1
                if file_exists:
                    with open(freelancers_csv, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Simple count of non-empty lines minus header
                        data_lines = [l for l in lines if l.strip() and ',' in l]
                        if len(data_lines) > 1: # Header + data
                            next_id_num = len(data_lines)
                
                year = datetime.now().year
                freelancer_id = f"FL-{year}-{next_id_num:04d}"
                
                # Append to CSV
                with open(freelancers_csv, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(['freelancer_id', 'full_name', 'email', 'registration_date'])
                    
                    writer.writerow([freelancer_id, user.name, user.email.lower(), datetime.now().isoformat()])
                    
            except Exception as e:
                logger.error(f"Freelancer ID generation failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to generate Freelancer ID")

        # Create new user
        new_user = User(
            name=user.name,
            email=user.email.lower(),
            password_hash=hash_password(user.password),
            phone=user.phone,
            dob=user.dob,
            state=user.state,
            city=user.city,
            pincode=user.pincode,

            mode="user",  # All signups are regular users
            employment_type=user.employment_type,
            employee_id=employee_id,
            freelancer_id=freelancer_id,
            
            ready_to_relocate=user.ready_to_relocate,
            preferred_location=user.preferred_location,
            notice_period=user.notice_period
        )
        
        # Insert into database
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"New user registered: {user.email} ({user.employment_type})")
        
        return UserResponse(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            mode=new_user.mode,
            employment_type=new_user.employment_type,
            employee_id=new_user.employee_id,
            freelancer_id=new_user.freelancer_id,
            created_at=new_user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        # Return more detailed error in development
        error_detail = str(e)
        if "users" in error_detail.lower() and "does not exist" in error_detail.lower():
            error_detail = "Database table 'users' does not exist. Please restart the backend to create tables."
        raise HTTPException(status_code=500, detail=f"Internal server error: {error_detail}")


@router.post("/admin-signup", response_model=UserResponse)
async def admin_signup(payload: AdminSignupRequest, db: AsyncSession = Depends(get_postgres_db)):
    """Register a new admin/staff user (Admin, Talent Acquisition, HR). Stored in DB for login."""
    try:
        # Check if user already exists
        query = select(User).where(User.email == payload.email.lower())
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=409, detail="User with this email already exists")

        # Map role to mode (stored in DB)
        role_lower = payload.role.strip().lower()
        if role_lower in ('admin', 'administrator'):
            mode = "admin"
        elif role_lower in ('talent acquisition', 'talent_acquisition', 'ta'):
            mode = "talent_acquisition"
        elif role_lower in ('hr', 'human resources'):
            mode = "hr"
        else:
            mode = "admin"  # Default

        if len(payload.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        if not payload.employee_id or not payload.employee_id.strip():
            raise HTTPException(status_code=400, detail="Employee ID is required for admin signup")

        config = await get_employee_list_config(db)
        if config.get("enabled", True) and not await is_employee_list_available(db):
            logger.error("Admin signup: company employee list not available")
            raise HTTPException(
                status_code=503,
                detail="Company employee list is not available. Please contact your administrator."
            )
        result = await verify_employee_against_list(payload.employee_id, payload.email, db)
        if config.get("enabled", True) and result is None:
            raise HTTPException(
                status_code=403,
                detail="Verification failed: this Employee ID and Email do not match any company record. Use the exact ID and email from your company list."
            )

        employee_id_clean = payload.employee_id.strip().upper()

        new_user = User(
            name=payload.name.strip(),
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            mode=mode,
            employee_id=employee_id_clean,
            employment_type=None,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"New admin user registered: {payload.email} (role={payload.role}, mode={mode})")

        return UserResponse(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            mode=new_user.mode,
            employment_type=new_user.employment_type,
            employee_id=new_user.employee_id,
            freelancer_id=new_user.freelancer_id,
            created_at=new_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin signup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-employee")
async def verify_employee(
    payload: VerifyEmployeeRequest,
    db: AsyncSession = Depends(get_postgres_db),
):
    """
    Verify employee ID and email against company list (uploaded or static CSV).
    No authentication required - used before upload in employee portal.
    """
    result = await verify_employee_against_list(payload.employee_id, payload.email, db)
    if result is not None:
        return {"valid": True, "full_name": result.get("full_name", "")}
    return {"valid": False, "message": "Employee ID and Email do not match company records"}


@router.post("/login")
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_postgres_db)):
    """Login user and return JWT token"""
    try:
        # Find user by email
        query = select(User).where(User.email == credentials.email.lower())
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email")
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        # Create JWT token
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "mode": user.mode or "user"
        }
        access_token = create_access_token(token_data)
        
        logger.info(f"User logged in: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "mode": user.mode or "user",
                "profile_img": user.profile_img,
                "employment_type": user.employment_type,
                "employee_id": user.employee_id,
                "freelancer_id": user.freelancer_id
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get current user information"""
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
            profile_img=user.profile_img,
            created_at=user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Logout user by blacklisting current JWT token"""
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        exp = None
        if payload and payload.get("exp"):
            try:
                exp = datetime.utcfromtimestamp(payload["exp"])
            except Exception:
                exp = None
        await blacklist_token(token, exp, db)
        logger.info(f"User logged out: {current_user['email']}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/forgot-password/send-code")
async def send_password_reset_code(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Send a password reset verification code to the user's email.
    """
    try:
        query = select(User).where(User.email == payload.email.lower())
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User with this email was not found")

        code = _generate_reset_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        _reset_tokens[payload.email.lower()] = {"code": code, "expires_at": expires_at}

        # For development: log the code so it can be used in the frontend
        logger.info(f"Password reset code for {payload.email}: {code}")

        return {"message": "Verification code sent to your email (simulated in server logs)."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending password reset code: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification code")


@router.post("/forgot-password/verify-code")
async def verify_password_reset_code(payload: VerifyCodeRequest):
    """
    Verify the password reset code for the given email.
    """
    try:
        record = _reset_tokens.get(payload.email.lower())
        if not record:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")

        if record["expires_at"] < datetime.utcnow():
            _reset_tokens.pop(payload.email.lower(), None)
            raise HTTPException(status_code=400, detail="Verification code has expired")

        if record["code"] != payload.code:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        return {"message": "Verification code is valid"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying password reset code: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify code")


@router.post("/forgot-password/reset")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Reset the user's password using a verified code.
    """
    try:
        record = _reset_tokens.get(payload.email.lower())
        if not record or record["code"] != payload.code or record["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")

        # Find user
        query = select(User).where(User.email == payload.email.lower())
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update password
        user.password_hash = hash_password(payload.new_password)
        await db.commit()
        await db.refresh(user)

        # Invalidate the used token
        _reset_tokens.pop(payload.email.lower(), None)

        logger.info(f"Password reset for user: {user.email}")
        return {"message": "Password has been reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")


# Google OAuth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.config.settings import settings

class GoogleLoginRequest(BaseModel):
    credential: str  # The ID token from Google



@router.post("/google-login")
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Login or Register with Google using ID Token.
    """
    try:
        # Verify the token
        try:
            id_info = id_token.verify_oauth2_token(
                payload.credential,
                google_requests.Request(),
                settings.google_client_id
            )
        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")

        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        email = email.lower()
        name = id_info.get("name", "Unknown")
        
        # Check if user exists
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            import secrets
            random_password = secrets.token_urlsafe(16)
            
            user = User(
                name=name,
                email=email,
                password_hash=hash_password(random_password),
                mode="user",
                source="google" if hasattr(User, "source") else None # Handle if source column missing
                # Add default values for other fields if necessary
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"New Google user registered: {email}")
        else:
            logger.info(f"Google user logged in: {email}")

        # Create JWT
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "mode": user.mode or "user"
        }
        access_token = create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "mode": user.mode or "user"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
