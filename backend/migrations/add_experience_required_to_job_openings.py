"""
Migration: Add experience_required column to job_openings table.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path so we can import from src
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
            logger.info("Adding experience_required column to job_openings...")
            await db.execute(text("""
                ALTER TABLE job_openings
                ADD COLUMN IF NOT EXISTS experience_required VARCHAR(20);
            """))
            await db.commit()
            logger.info("Column experience_required added successfully.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Migration failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
