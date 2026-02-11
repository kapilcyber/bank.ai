"""
Migration: Add sector and domain columns to experiences table

This migration adds sector identification fields to the experiences table
to track the industry sector and domain of each company.
"""

import asyncio
from sqlalchemy import text
from src.config.database import engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def upgrade():
    """Add sector and domain columns to experiences table."""
    try:
        async with engine.begin() as conn:
            # Add sector column
            await conn.execute(text("""
                ALTER TABLE experiences 
                ADD COLUMN IF NOT EXISTS sector VARCHAR(100)
            """))
            
            # Add domain column
            await conn.execute(text("""
                ALTER TABLE experiences 
                ADD COLUMN IF NOT EXISTS domain VARCHAR(100)
            """))
            
        logger.info("Successfully added sector and domain columns to experiences table")
        print("✅ Migration completed: Added sector and domain columns to experiences table")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        raise


async def downgrade():
    """Remove sector and domain columns from experiences table."""
    try:
        async with engine.begin() as conn:
            # Remove sector column
            await conn.execute(text("""
                ALTER TABLE experiences 
                DROP COLUMN IF EXISTS sector
            """))
            
            # Remove domain column
            await conn.execute(text("""
                ALTER TABLE experiences 
                DROP COLUMN IF EXISTS domain
            """))
            
        logger.info("Successfully removed sector and domain columns from experiences table")
        print("✅ Rollback completed: Removed sector and domain columns from experiences table")
            
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        print(f"❌ Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("Running downgrade migration...")
        asyncio.run(downgrade())
    else:
        print("Running upgrade migration...")
        asyncio.run(upgrade())
