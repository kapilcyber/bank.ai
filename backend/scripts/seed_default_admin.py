"""
One-time script to create or update the default admin user so you can log in.
Run from backend directory: python -m scripts.seed_default_admin

Set environment variables (do not commit passwords to repo):
  DEFAULT_ADMIN_EMAIL=shweta_gaba@cachedigitech.com
  DEFAULT_ADMIN_PASSWORD=Cache@1993

Or on Windows CMD:
  set DEFAULT_ADMIN_EMAIL=shweta_gaba@cachedigitech.com
  set DEFAULT_ADMIN_PASSWORD=Cache@1993
  python -m scripts.seed_default_admin
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure backend root is on path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# Load .env from backend root
from dotenv import load_dotenv
load_dotenv(backend_root / ".env")

from sqlalchemy import select
from src.config.database import AsyncSessionLocal
from src.models.user_db import User
from src.routes.auth import hash_password


async def seed_default_admin():
    email = (os.environ.get("DEFAULT_ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "").strip()

    if not email or not password:
        print("Usage: Set DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD environment variables.")
        print("Example (Windows CMD):")
        print("  set DEFAULT_ADMIN_EMAIL=shweta_gaba@cachedigitech.com")
        print("  set DEFAULT_ADMIN_PASSWORD=YourPassword")
        print("  python -m scripts.seed_default_admin")
        print("Example (PowerShell):")
        print("  $env:DEFAULT_ADMIN_EMAIL='shweta_gaba@cachedigitech.com'; $env:DEFAULT_ADMIN_PASSWORD='YourPassword'; python -m scripts.seed_default_admin")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        sys.exit(1)

    name = email.split("@")[0].replace(".", " ").replace("_", " ").title() or "Admin"

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user:
                user.password_hash = hash_password(password)
                user.mode = "admin"
                user.name = name
                await session.commit()
                await session.refresh(user)
                print(f"Updated existing user: {email} (mode=admin, password reset). You can now log in.")
            else:
                user = User(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    mode="admin",
                    employment_type=None,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(f"Created default admin: {email}. You can now log in.")
        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_default_admin())
