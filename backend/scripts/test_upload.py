"""
Test script to verify resume upload and count
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from src.models.resume import Resume
from src.config.settings import settings

async def test_count():
    """Test resume count before and after operations"""
    try:
        engine = create_async_engine(
            settings.async_database_url,
            pool_pre_ping=True,
            echo=False
        )
        
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with AsyncSessionLocal() as db:
            print("=" * 80)
            print("RESUME COUNT TEST")
            print("=" * 80)
            
            # Count total resumes
            count_result = await db.execute(select(func.count(Resume.id)))
            total_count = count_result.scalar()
            
            print(f"\n[INFO] Current total resumes in database: {total_count}")
            
            # Get latest 5 resumes
            latest_query = select(Resume).order_by(Resume.uploaded_at.desc()).limit(5)
            latest_result = await db.execute(latest_query)
            latest_resumes = latest_result.scalars().all()
            
            print(f"\n[INFO] Latest 5 resumes:")
            for i, resume in enumerate(latest_resumes, 1):
                print(f"   {i}. ID: {resume.id}, Filename: {resume.filename}, Uploaded: {resume.uploaded_at}, Source: {resume.source_type}")
            
            # Check for admin uploads
            admin_query = select(func.count(Resume.id)).where(Resume.source_type == 'admin')
            admin_result = await db.execute(admin_query)
            admin_count = admin_result.scalar()
            
            print(f"\n[INFO] Admin uploads: {admin_count}")
            
            print("\n" + "=" * 80)
            print("If you just uploaded a resume and count didn't increase:")
            print("1. Check backend logs for errors")
            print("2. Verify the upload endpoint returned success")
            print("3. Check if resume was actually saved (see latest resumes above)")
            print("4. Restart backend server if code was changed")
            print("=" * 80)
            
        await engine.dispose()
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_count())
