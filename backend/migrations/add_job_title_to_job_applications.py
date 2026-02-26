"""
Migration: Add job_title column to job_applications table.
Stores the job opening title at the time of application for display/history.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.config.database import AsyncSessionLocal
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def migrate():
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Adding job_title column to job_applications...")
            await db.execute(text("""
                ALTER TABLE job_applications
                ADD COLUMN IF NOT EXISTS job_title VARCHAR(255);
            """))
            await db.commit()
            logger.info("Column job_title added successfully.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Migration failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
