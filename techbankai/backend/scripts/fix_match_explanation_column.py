"""
Script to fix match_explanation column type from VARCHAR(100) to TEXT.
Run this script to update the database schema to match the model definition.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.database import get_postgres_db
from src.config.settings import settings
from sqlalchemy import text
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def fix_match_explanation_column():
    """Fix match_explanation column type from VARCHAR(100) to TEXT."""
    try:
        async for db in get_postgres_db():
            try:
                # Check current column type
                check_query = text("""
                    SELECT data_type, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = 'match_results'
                    AND column_name = 'match_explanation'
                """)
                result = await db.execute(check_query)
                row = result.fetchone()
                
                if row:
                    data_type, max_length = row
                    logger.info(f"Current match_explanation column type: {data_type}({max_length})")
                    
                    if data_type == 'character varying' and max_length == 100:
                        # Alter column to TEXT
                        alter_query = text("""
                            ALTER TABLE match_results
                            ALTER COLUMN match_explanation TYPE TEXT
                        """)
                        await db.execute(alter_query)
                        await db.commit()
                        logger.info("✅ Successfully changed match_explanation column from VARCHAR(100) to TEXT")
                    elif data_type == 'text':
                        logger.info("✅ Column match_explanation is already TEXT")
                    else:
                        logger.warning(f"⚠️ Column match_explanation has unexpected type: {data_type}({max_length})")
                else:
                    logger.error("❌ Column match_explanation not found in match_results table")
                
            except Exception as e:
                logger.error(f"Error fixing match_explanation column: {e}", exc_info=True)
                await db.rollback()
                raise
            finally:
                break  # Exit the async generator
                
    except Exception as e:
        logger.error(f"Failed to fix match_explanation column: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    print("🔧 Fixing match_explanation column type...")
    asyncio.run(fix_match_explanation_column())
    print("✅ Done!")
