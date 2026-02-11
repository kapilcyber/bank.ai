"""
Migration: Add file_content and file_mime_type columns to resumes table.
Also migrate existing files from filesystem to database.
"""
import asyncio
import aiofiles
import sys
from pathlib import Path
from sqlalchemy import text, select

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.config.database import AsyncSessionLocal
from src.models.resume import Resume
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def migrate():
    """Run migration."""
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Add new columns
            logger.info("Adding file_content and file_mime_type columns...")
            await db.execute(text("""
                ALTER TABLE resumes 
                ADD COLUMN IF NOT EXISTS file_content BYTEA,
                ADD COLUMN IF NOT EXISTS file_mime_type VARCHAR(100);
            """))
            await db.commit()
            logger.info("Columns added successfully")
            
            # Step 2: Migrate existing files from filesystem to database
            logger.info("Migrating existing files from filesystem to database...")
            query = select(Resume).where(Resume.file_content.is_(None))
            result = await db.execute(query)
            resumes = result.scalars().all()
            
            migrated_count = 0
            skipped_count = 0
            
            for resume in resumes:
                try:
                    # Extract file path from file_url
                    if resume.file_url and resume.file_url.startswith('/uploads/'):
                        # Remove leading slash and construct path
                        file_path = Path(resume.file_url.lstrip('/'))
                        
                        if file_path.exists():
                            # Read file content
                            async with aiofiles.open(file_path, 'rb') as f:
                                content = await f.read()
                            
                            # Determine MIME type from filename
                            ext = resume.filename.split('.')[-1].lower() if resume.filename else 'pdf'
                            mime_type = 'application/pdf' if ext == 'pdf' else \
                                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if ext == 'docx' else \
                                       'application/msword' if ext == 'doc' else \
                                       'application/octet-stream'
                            
                            # Update resume with file content
                            resume.file_content = content
                            resume.file_mime_type = mime_type
                            resume.file_url = f"/api/resumes/{resume.id}/file"
                            
                            migrated_count += 1
                            logger.info(f"Migrated resume ID {resume.id}: {resume.filename}")
                        else:
                            skipped_count += 1
                            logger.warning(f"File not found for resume ID {resume.id}: {file_path}")
                    elif resume.file_url and ('drive.google.com' in resume.file_url or 'gdrive' in resume.file_url.lower()):
                        # Skip Google Drive files - they're already stored externally
                        skipped_count += 1
                        logger.info(f"Skipping Google Drive file for resume ID {resume.id}")
                    else:
                        skipped_count += 1
                        logger.info(f"Skipping resume ID {resume.id}: file_url is not a local path ({resume.file_url})")
                
                except Exception as e:
                    logger.error(f"Error migrating resume ID {resume.id}: {e}")
                    skipped_count += 1
                    continue
            
            await db.commit()
            logger.info(f"Migration complete! Migrated {migrated_count} files to database, skipped {skipped_count} files")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Migration failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())

