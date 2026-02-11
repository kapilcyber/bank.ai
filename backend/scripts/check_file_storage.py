"""
Check which resumes have file_content in database vs filesystem-only.
This helps identify resumes that need to be re-uploaded.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from src.config.database import AsyncSessionLocal
from src.models.resume import Resume
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def check_storage():
    """Check resume file storage status."""
    async with AsyncSessionLocal() as db:
        try:
            print("=" * 80)
            print("RESUME FILE STORAGE DIAGNOSTIC")
            print("=" * 80)
            
            # Count total resumes
            total_result = await db.execute(select(func.count(Resume.id)))
            total_count = total_result.scalar()
            print(f"\n[INFO] Total resumes in database: {total_count}")
            
            # Count resumes with file_content
            with_content_result = await db.execute(
                select(func.count(Resume.id)).where(Resume.file_content.isnot(None))
            )
            count_with_content = with_content_result.scalar()
            print(f"[OK] Resumes with file_content in DB: {count_with_content}")
            
            # Count resumes without file_content
            without_content_result = await db.execute(
                select(func.count(Resume.id)).where(Resume.file_content.is_(None))
            )
            count_without_content = without_content_result.scalar()
            print(f"[WARNING] Resumes without file_content (filesystem only): {count_without_content}")
            
            # Calculate percentage
            if total_count > 0:
                pct_with_content = (count_with_content / total_count) * 100
                pct_without_content = (count_without_content / total_count) * 100
                print(f"\n[STATS] Storage coverage:")
                print(f"  - In database: {pct_with_content:.1f}%")
                print(f"  - Filesystem only: {pct_without_content:.1f}%")
            
            # Show sample of resumes without file_content
            if count_without_content > 0:
                print("\n" + "=" * 80)
                print("SAMPLE RESUMES WITHOUT file_content (first 20):")
                print("=" * 80)
                query = select(
                    Resume.id,
                    Resume.filename,
                    Resume.file_url,
                    Resume.source_type,
                    Resume.uploaded_at
                ).where(
                    Resume.file_content.is_(None)
                ).order_by(Resume.uploaded_at.desc()).limit(20)
                
                result = await db.execute(query)
                print(f"\n{'ID':<8} {'Filename':<40} {'Source':<15} {'Uploaded':<20} {'file_url'}")
                print("-" * 120)
                
                for row in result:
                    file_url_short = row.file_url[:50] + "..." if row.file_url and len(row.file_url) > 50 else (row.file_url or "N/A")
                    uploaded_str = row.uploaded_at.strftime("%Y-%m-%d %H:%M") if row.uploaded_at else "N/A"
                    print(f"{row.id:<8} {row.filename[:40]:<40} {row.source_type:<15} {uploaded_str:<20} {file_url_short}")
                
                if count_without_content > 20:
                    print(f"\n... and {count_without_content - 20} more resumes without file_content")
            
            # Check file_url patterns
            print("\n" + "=" * 80)
            print("FILE_URL PATTERN ANALYSIS:")
            print("=" * 80)
            
            # Count by file_url pattern
            api_endpoint_result = await db.execute(
                select(func.count(Resume.id)).where(
                    Resume.file_url.like('/api/resumes/%/file')
                )
            )
            api_count = api_endpoint_result.scalar()
            
            uploads_path_result = await db.execute(
                select(func.count(Resume.id)).where(
                    Resume.file_url.like('/uploads/%')
                )
            )
            uploads_count = uploads_path_result.scalar()
            
            http_url_result = await db.execute(
                select(func.count(Resume.id)).where(
                    Resume.file_url.like('http%')
                )
            )
            http_count = http_url_result.scalar()
            
            print(f"  - API endpoints (/api/resumes/.../file): {api_count}")
            print(f"  - Filesystem paths (/uploads/...): {uploads_count}")
            print(f"  - HTTP/HTTPS URLs: {http_count}")
            
            # Recommendations
            print("\n" + "=" * 80)
            print("RECOMMENDATIONS:")
            print("=" * 80)
            
            if count_without_content > 0:
                print(f"\n[ACTION REQUIRED] {count_without_content} resumes need attention:")
                print("  1. If files still exist on filesystem, run migration script:")
                print("     python backend/migrations/add_file_content_to_resumes.py")
                print("  2. If files are deleted, re-upload those resumes")
                print("  3. New uploads automatically store files in database")
            else:
                print("\n[OK] All resumes have file_content stored in database!")
            
            print("\n" + "=" * 80)
            
        except Exception as e:
            logger.error(f"Error checking storage: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    print("Starting resume file storage diagnostic...\n")
    asyncio.run(check_storage())

