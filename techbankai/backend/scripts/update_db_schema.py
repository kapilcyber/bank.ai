import asyncio
from sqlalchemy import text
from src.config.database import AsyncSessionLocal

async def update_schema():
    async with AsyncSessionLocal() as db:
        try:
            print("Updating resumes table source_id column size...")
            await db.execute(text("ALTER TABLE resumes ALTER COLUMN source_id TYPE VARCHAR(500)"))
            
            print("Updating match_results table source_id column size...")
            await db.execute(text("ALTER TABLE match_results ALTER COLUMN source_id TYPE VARCHAR(500)"))
            
            await db.commit()
            print("Successfully updated source_id column sizes to 500.")
        except Exception as e:
            print(f"Error updating schema: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(update_schema())

