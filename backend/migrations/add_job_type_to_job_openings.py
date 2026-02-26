"""
Migration: Add job_type column to job_openings table.
Values: internship, full_time, remote, hybrid, contract
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
    """Run migration."""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Adding job_type column to job_openings...")
            await db.execute(text("""
                ALTER TABLE job_openings
                ADD COLUMN IF NOT EXISTS job_type VARCHAR(50);
            """))
            await db.commit()
            logger.info("Column job_type added successfully.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Migration failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
