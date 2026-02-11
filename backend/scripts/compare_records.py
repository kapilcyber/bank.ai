"""
Script to compare current database records with previous state
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from src.models.resume import Resume
from src.config.settings import settings

async def compare_records():
    """Compare current database state"""
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
            print("CURRENT DATABASE RECORDS ANALYSIS")
            print("=" * 80)
            
            # Count total resumes
            count_result = await db.execute(select(func.count(Resume.id)))
            total_count = count_result.scalar()
            print(f"\n[INFO] Total resumes in database: {total_count}")
            
            # Get all resumes ordered by upload date
            all_query = select(Resume).order_by(Resume.uploaded_at.desc())
            all_result = await db.execute(all_query)
            all_resumes = all_result.scalars().all()
            
            print(f"\n[INFO] All {len(all_resumes)} resumes (newest first):")
            print("-" * 80)
            
            for i, resume in enumerate(all_resumes, 1):
                # Extract candidate name from parsed_data
                candidate_name = "Unknown"
                if resume.parsed_data:
                    candidate_name = (
                        resume.parsed_data.get('resume_candidate_name') or 
                        resume.parsed_data.get('name') or 
                        resume.parsed_data.get('fullName') or 
                        "Unknown"
                    )
                
                # Extract email
                email = "No Email"
                if resume.parsed_data:
                    email_val = (
                        resume.parsed_data.get('resume_contact_info') or
                        resume.parsed_data.get('email') or
                        None
                    )
                    if email_val:
                        email = str(email_val) if not isinstance(email_val, dict) else "No Email"
                
                # Get user type
                from src.utils.user_type_mapper import normalize_user_type, get_user_type_from_source_type
                meta = resume.meta_data or {}
                user_type = normalize_user_type(meta.get('user_type') or get_user_type_from_source_type(resume.source_type))
                
                # Extract role
                role = "N/A"
                if resume.parsed_data:
                    role = resume.parsed_data.get('resume_role') or resume.parsed_data.get('role') or "N/A"
                
                candidate_display = (candidate_name[:20] if len(candidate_name) > 20 else candidate_name).ljust(20)
                email_display = (email[:30] if len(email) > 30 else email).ljust(30)
                role_display = (role[:25] if len(role) > 25 else role).ljust(25)
                print(f"#{i:2d} | ID:{resume.id:3d} | {candidate_display} | {email_display} | {user_type:20s} | {role_display} | Uploaded: {resume.uploaded_at}")
            
            # Breakdown by type
            print("\n" + "=" * 80)
            print("BREAKDOWN BY USER TYPE")
            print("=" * 80)
            
            from src.utils.user_type_mapper import normalize_user_type, get_user_type_from_source_type
            type_counts = {}
            for resume in all_resumes:
                meta = resume.meta_data or {}
                user_type = normalize_user_type(meta.get('user_type') or get_user_type_from_source_type(resume.source_type))
                type_counts[user_type] = type_counts.get(user_type, 0) + 1
            
            for user_type, count in sorted(type_counts.items()):
                print(f"  {user_type:25s}: {count:3d}")
            
            # Check for duplicates by email
            print("\n" + "=" * 80)
            print("CHECKING FOR DUPLICATE EMAILS")
            print("=" * 80)
            
            email_map = {}
            for resume in all_resumes:
                if resume.parsed_data:
                    email = (
                        resume.parsed_data.get('resume_contact_info') or
                        resume.parsed_data.get('email') or
                        None
                    )
                    if email and email != "No Email":
                        if email not in email_map:
                            email_map[email] = []
                        email_map[email].append(resume.id)
            
            duplicates = {email: ids for email, ids in email_map.items() if len(ids) > 1}
            if duplicates:
                print(f"[WARNING] Found {len(duplicates)} emails with multiple resumes:")
                for email, ids in duplicates.items():
                    print(f"  {email}: Resume IDs {ids}")
            else:
                print("[OK] No duplicate emails found")
            
            print("\n" + "=" * 80)
            
        await engine.dispose()
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(compare_records())
