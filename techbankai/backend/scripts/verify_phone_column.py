"""Script to verify phone column exists in users table."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.config.database import engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def verify_phone_column():
    """Verify phone column exists in users table."""
    try:
        async with engine.begin() as conn:
            # Check if column exists
            check_query = text("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'phone'
            """)
            result = await conn.execute(check_query)
            column_info = result.fetchone()
            
            if column_info:
                logger.info(f"✓ Phone column exists:")
                logger.info(f"  - Name: {column_info[0]}")
                logger.info(f"  - Type: {column_info[1]}")
                logger.info(f"  - Max Length: {column_info[2]}")
                logger.info(f"  - Nullable: {column_info[3]}")
                return True
            else:
                logger.error("✗ Phone column does NOT exist in users table")
                return False
                
    except Exception as e:
        logger.error(f"Error verifying phone column: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """Main function."""
    exists = await verify_phone_column()
    sys.exit(0 if exists else 1)


if __name__ == "__main__":
    asyncio.run(main())
