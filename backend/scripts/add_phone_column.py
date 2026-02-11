"""Script to add phone column to users table."""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.config.database import engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def add_phone_column():
    """Add phone column to users table if it doesn't exist."""
    try:
        async with engine.begin() as conn:
            # Check if column exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'phone'
            """)
            result = await conn.execute(check_query)
            column_exists = result.scalar_one_or_none() is not None
            
            if column_exists:
                logger.info("Phone column already exists in users table")
                return
            
            # Add the column
            alter_query = text("""
                ALTER TABLE users 
                ADD COLUMN phone VARCHAR(20);
            """)
            await conn.execute(alter_query)
            logger.info("Successfully added phone column to users table")
            
            # Add comment
            comment_query = text("""
                COMMENT ON COLUMN users.phone IS 'User phone number (10-20 characters)';
            """)
            await conn.execute(comment_query)
            logger.info("Added comment to phone column")
            
    except Exception as e:
        logger.error(f"Error adding phone column: {e}")
        raise


async def main():
    """Main function."""
    logger.info("Starting phone column migration...")
    try:
        await add_phone_column()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
