"""
Script to verify resume records in the database and compare with admin portal count.
This helps diagnose why records might not be visible in the database.
"""
import asyncio
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from src.models.resume import Resume
from src.config.settings import settings

async def verify_resumes():
    """Verify resume records in the database."""
    try:
        # Create database engine
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
            print("DATABASE VERIFICATION REPORT")
            print("=" * 80)
            print()
            
            # 1. Check database connection
            print("1. Testing database connection...")
            try:
                result = await db.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"   [OK] Connected to PostgreSQL: {version.split(',')[0]}")
            except Exception as e:
                print(f"   [ERROR] Connection failed: {e}")
                return
            
            # 2. Check current database name
            print("\n2. Checking current database...")
            try:
                result = await db.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                print(f"   📊 Current database: {db_name}")
            except Exception as e:
                print(f"   ⚠️  Could not get database name: {e}")
            
            # 3. Count total resumes
            print("\n3. Counting total resumes in 'resumes' table...")
            try:
                count_result = await db.execute(select(func.count(Resume.id)))
                total_count = count_result.scalar()
                print(f"   📈 Total resumes in database: {total_count}")
            except Exception as e:
                print(f"   [ERROR] Error counting resumes: {e}")
                return
            
            # 4. Get recent resumes (same query as admin portal)
            print("\n4. Fetching recent resumes (same as admin portal)...")
            try:
                recent_query = select(Resume).options(
                    selectinload(Resume.work_history),
                    selectinload(Resume.certificates),
                    selectinload(Resume.educations)
                ).order_by(Resume.uploaded_at.desc())
                
                recent_result = await db.execute(recent_query)
                recent_resumes = recent_result.scalars().all()
                
                print(f"   📋 Total resumes fetched: {len(recent_resumes)}")
                print(f"   📋 Limited to first 50 (admin portal limit): {min(50, len(recent_resumes))}")
                
                if len(recent_resumes) > 0:
                    print("\n   Sample of recent resumes:")
                    for i, resume in enumerate(recent_resumes[:10], 1):
                        print(f"   {i}. ID: {resume.id}, Uploaded: {resume.uploaded_at}, Source: {resume.source_type}")
            except Exception as e:
                print(f"   [ERROR] Error fetching recent resumes: {e}")
            
            # 5. Check for resumes by source type
            print("\n5. Breakdown by source type...")
            try:
                source_types_query = select(
                    Resume.source_type,
                    func.count(Resume.id).label('count')
                ).group_by(Resume.source_type)
                
                source_result = await db.execute(source_types_query)
                source_breakdown = source_result.all()
                
                for source_type, count in source_breakdown:
                    print(f"   - {source_type or 'NULL'}: {count}")
            except Exception as e:
                print(f"   [ERROR] Error getting source type breakdown: {e}")
            
            # 6. Check table structure
            print("\n6. Verifying table structure...")
            try:
                table_info = await db.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'resumes'
                    ORDER BY ordinal_position
                """))
                columns = table_info.all()
                print(f"   📋 Table 'resumes' has {len(columns)} columns:")
                for col_name, col_type in columns[:10]:  # Show first 10
                    print(f"      - {col_name}: {col_type}")
                if len(columns) > 10:
                    print(f"      ... and {len(columns) - 10} more columns")
            except Exception as e:
                print(f"   ⚠️  Could not get table structure: {e}")
            
            # 7. Check for any NULL or missing data
            print("\n7. Checking data quality...")
            try:
                null_checks = await db.execute(text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(id) as has_id,
                        COUNT(uploaded_at) as has_upload_date,
                        COUNT(source_type) as has_source_type
                    FROM resumes
                """))
                null_data = null_checks.one()
                print(f"   Total rows: {null_data.total}")
                print(f"   Rows with ID: {null_data.has_id}")
                print(f"   Rows with upload date: {null_data.has_upload_date}")
                print(f"   Rows with source type: {null_data.has_source_type}")
            except Exception as e:
                print(f"   ⚠️  Could not check data quality: {e}")
            
            # 8. SQL query to run manually
            print("\n" + "=" * 80)
            print("MANUAL VERIFICATION QUERIES")
            print("=" * 80)
            print("\nTo verify in pgAdmin or psql, run these queries:")
            print("\n1. Count all resumes:")
            print("   SELECT COUNT(*) FROM resumes;")
            print("\n2. See all resumes:")
            print("   SELECT id, uploaded_at, source_type FROM resumes ORDER BY uploaded_at DESC;")
            print("\n3. See recent 40 resumes:")
            print("   SELECT id, uploaded_at, source_type FROM resumes ORDER BY uploaded_at DESC LIMIT 40;")
            print("\n4. Check if table exists:")
            print("   SELECT table_name FROM information_schema.tables WHERE table_name = 'resumes';")
            print("\n5. Check database name:")
            print("   SELECT current_database();")
            print("\n" + "=" * 80)
            
            if total_count == 0:
                print("\n[WARNING] No resumes found in database!")
                print("   Possible issues:")
                print("   1. Wrong database connection")
                print("   2. Data not saved properly")
                print("   3. Table not created")
                print("   4. Data in different database")
            elif total_count < 40:
                print(f"\n[WARNING] Found {total_count} resumes, but admin portal shows 40!")
                print("   This might indicate:")
                print("   1. Some records are cached in frontend")
                print("   2. Multiple databases exist")
                print("   3. Connection to different database")
            else:
                print(f"\n[OK] Found {total_count} resumes in database.")
                print("   If admin portal shows 40, it's showing the latest 40 records.")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting database verification...")
    asyncio.run(verify_resumes())
