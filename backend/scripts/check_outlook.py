import asyncio
from sqlalchemy import select
from src.config.database import AsyncSessionLocal
from src.models.resume import Resume

async def check_outlook_resumes():
    async with AsyncSessionLocal() as db:
        query = select(Resume).where(Resume.source_type == 'outlook').order_by(Resume.uploaded_at.desc())
        result = await db.execute(query)
        resumes = result.scalars().all()
        
        print(f"Total Outlook resumes found: {len(resumes)}")
        for r in resumes:
            print(f"- ID: {r.id}, Name: {r.filename}, Created: {r.uploaded_at}, Sender: {r.source_metadata.get('sender_email')}")

if __name__ == "__main__":
    asyncio.run(check_outlook_resumes())

