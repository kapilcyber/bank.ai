"""Script to fix source_id column size in resumes table."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import engine
from sqlalchemy import text
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def fix_source_id_column():
    """Alter source_id column from VARCHAR(100) to VARCHAR(500)."""
    try:
        async with engine.begin() as conn:
            # Check current column definition
            check_query = text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'resumes' 
                AND column_name = 'source_id'
                AND data_type = 'character varying'
            """)
            
            result = await conn.execute(check_query)
            row = result.fetchone()
            
            if row:
                current_length = row[0]
                logger.info(f"Current source_id column length: {current_length}")
                
                if current_length == 100:
                    # Alter the column
                    alter_query = text("""
                        ALTER TABLE resumes 
                        ALTER COLUMN source_id TYPE VARCHAR(500)
                    """)
                    await conn.execute(alter_query)
                    logger.info("Successfully changed source_id column from VARCHAR(100) to VARCHAR(500)")
                elif current_length == 500:
                    logger.info("source_id column is already VARCHAR(500), no changes needed")
                else:
                    logger.warning(f"source_id column has unexpected length: {current_length}. Altering to VARCHAR(500)")
                    alter_query = text("""
                        ALTER TABLE resumes 
                        ALTER COLUMN source_id TYPE VARCHAR(500)
                    """)
                    await conn.execute(alter_query)
                    logger.info("Successfully changed source_id column to VARCHAR(500)")
            else:
                logger.warning("source_id column not found or is not VARCHAR type")
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing source_id column: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_source_id_column())

