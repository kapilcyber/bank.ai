"""
Populate file_content for resumes from a reference folder.
Matches files to database records and updates them.
"""
import asyncio
import sys
import argparse
from pathlib import Path
from difflib import SequenceMatcher

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiofiles
from sqlalchemy import select
from src.config.database import AsyncSessionLocal
from src.models.resume import Resume
from src.utils.logger import get_logger

logger = get_logger(__name__)


def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalize_filename(filename: str) -> str:
    """Normalize filename for matching (remove common prefixes/suffixes)."""
    # Remove common prefixes/suffixes that might differ
    name = filename.lower().strip()
    # Remove file extension
    if '.' in name:
        name = name.rsplit('.', 1)[0]
    # Remove common prefixes
    prefixes = ['resume_', 'resume-', 'cv_', 'cv-', 'naukri_']
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name.strip()


async def find_matching_resume(file_path: Path, resumes_without_content: list) -> tuple:
    """
    Find the best matching resume record for a file.
    Returns (resume, similarity_score) or (None, 0.0) if no good match.
    """
    file_name = file_path.name
    file_name_normalized = normalize_filename(file_name)
    
    best_match = None
    best_score = 0.0
    
    for resume in resumes_without_content:
        # Try exact filename match first
        if resume.filename.lower() == file_name.lower():
            return (resume, 1.0)
        
        # Try normalized match
        resume_name_normalized = normalize_filename(resume.filename)
        if resume_name_normalized == file_name_normalized:
            return (resume, 0.95)
        
        # Try similarity matching
        score = similarity(resume.filename, file_name)
        if score > best_score:
            best_score = score
            best_match = resume
    
    # Only return if similarity is high enough (>= 0.7)
    if best_score >= 0.7:
        return (best_match, best_score)
    
    return (None, 0.0)


def get_mime_type(filename: str) -> str:
    """Determine MIME type from filename extension."""
    ext = filename.split('.')[-1].lower() if '.' in filename else 'pdf'
    mime_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
    }
    return mime_types.get(ext, 'application/octet-stream')


async def populate_from_folder(folder_path: str, min_similarity: float = 0.7, dry_run: bool = False):
    """
    Populate file_content for resumes from a folder.
    
    Args:
        folder_path: Path to folder containing resume files
        min_similarity: Minimum similarity score for matching (0.0-1.0)
        dry_run: If True, only show what would be done without updating database
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"[ERROR] Folder does not exist: {folder_path}")
        return
    
    if not folder.is_dir():
        print(f"[ERROR] Path is not a directory: {folder_path}")
        return
    
    # Find all PDF and DOCX files
    pdf_files = list(folder.glob("*.pdf"))
    docx_files = list(folder.glob("*.docx"))
    doc_files = list(folder.glob("*.doc"))
    all_files = pdf_files + docx_files + doc_files
    
    print("=" * 80)
    print("POPULATE RESUMES FROM FOLDER")
    print("=" * 80)
    print(f"\n[INFO] Scanning folder: {folder_path}")
    print(f"[INFO] Found {len(all_files)} resume files ({len(pdf_files)} PDF, {len(docx_files)} DOCX, {len(doc_files)} DOC)")
    
    if len(all_files) == 0:
        print("[WARNING] No resume files found in folder!")
        return
    
    async with AsyncSessionLocal() as db:
        # Get all resumes without file_content
        query = select(Resume).where(Resume.file_content.is_(None))
        result = await db.execute(query)
        resumes_without_content = result.scalars().all()
        
        print(f"[INFO] Found {len(resumes_without_content)} resumes in database without file_content")
        
        if len(resumes_without_content) == 0:
            print("[OK] All resumes already have file_content!")
            return
        
        # Match files to resumes
        matches = []
        unmatched_files = []
        matched_resume_ids = set()
        
        print("\n" + "=" * 80)
        print("MATCHING FILES TO DATABASE RECORDS:")
        print("=" * 80)
        
        for file_path in all_files:
            resume, score = await find_matching_resume(file_path, resumes_without_content)
            
            if resume and score >= min_similarity:
                # Check if this resume was already matched
                if resume.id in matched_resume_ids:
                    print(f"[SKIP] {file_path.name} -> Resume ID {resume.id} ({resume.filename}) [ALREADY MATCHED]")
                    unmatched_files.append((file_path, f"Already matched to resume ID {resume.id}"))
                else:
                    matches.append((file_path, resume, score))
                    matched_resume_ids.add(resume.id)
                    print(f"[MATCH] {file_path.name} -> Resume ID {resume.id} ({resume.filename}) [Score: {score:.2f}]")
            else:
                unmatched_files.append((file_path, f"No match found (best score: {score:.2f})"))
                print(f"[NO MATCH] {file_path.name} [Best score: {score:.2f}]")
        
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Total files: {len(all_files)}")
        print(f"Matched: {len(matches)}")
        print(f"Unmatched: {len(unmatched_files)}")
        print(f"Resumes still missing file_content: {len(resumes_without_content) - len(matches)}")
        
        if len(matches) == 0:
            print("\n[WARNING] No files matched! Check filenames.")
            return
        
        # Show unmatched files for review
        if unmatched_files:
            print("\n" + "=" * 80)
            print("UNMATCHED FILES (for manual review):")
            print("=" * 80)
            for file_path, reason in unmatched_files[:20]:  # Show first 20
                print(f"  - {file_path.name}: {reason}")
            if len(unmatched_files) > 20:
                print(f"  ... and {len(unmatched_files) - 20} more")
        
        # Update database
        if dry_run:
            print("\n" + "=" * 80)
            print("[DRY RUN] Would update the following resumes:")
            print("=" * 80)
            for file_path, resume, score in matches:
                file_size = file_path.stat().st_size
                print(f"  Resume ID {resume.id}: {resume.filename}")
                print(f"    <- File: {file_path.name} ({file_size:,} bytes, score: {score:.2f})")
            print("\n[DRY RUN] No changes made. Run without --dry-run to apply changes.")
        else:
            print("\n" + "=" * 80)
            print("UPDATING DATABASE:")
            print("=" * 80)
            
            updated_count = 0
            error_count = 0
            
            for file_path, resume, score in matches:
                try:
                    # Read file content
                    async with aiofiles.open(file_path, 'rb') as f:
                        content = await f.read()
                    
                    # Determine MIME type
                    mime_type = get_mime_type(file_path.name)
                    
                    # Update resume
                    resume.file_content = content
                    resume.file_mime_type = mime_type
                    resume.file_url = f"/api/resumes/{resume.id}/file"
                    
                    updated_count += 1
                    file_size = len(content)
                    print(f"[OK] Updated Resume ID {resume.id}: {resume.filename} ({file_size:,} bytes)")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error updating resume ID {resume.id}: {e}")
                    print(f"[ERROR] Failed to update Resume ID {resume.id}: {e}")
            
            # Commit all changes
            try:
                await db.commit()
                print("\n" + "=" * 80)
                print("UPDATE COMPLETE!")
                print("=" * 80)
                print(f"[OK] Successfully updated {updated_count} resumes")
                if error_count > 0:
                    print(f"[WARNING] {error_count} updates failed")
            except Exception as e:
                await db.rollback()
                logger.error(f"Error committing changes: {e}")
                print(f"\n[ERROR] Failed to commit changes: {e}")
                raise


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Populate file_content for resumes from a folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (see what would be done)
  python scripts/populate_resumes_from_folder.py "C:/Users/Admin/Downloads/techbankai/RESUME FOLDER" --dry-run
  
  # Actually update database
  python scripts/populate_resumes_from_folder.py "C:/Users/Admin/Downloads/techbankai/RESUME FOLDER"
  
  # Use custom similarity threshold
  python scripts/populate_resumes_from_folder.py "C:/Users/Admin/Downloads/techbankai/RESUME FOLDER" --min-similarity 0.8
        """
    )
    parser.add_argument(
        "folder",
        help="Path to folder containing resume files"
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.7,
        help="Minimum similarity score for matching (0.0-1.0, default: 0.7)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without updating database"
    )
    
    args = parser.parse_args()
    
    await populate_from_folder(
        args.folder,
        min_similarity=args.min_similarity,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    print("Starting resume population from folder...\n")
    asyncio.run(main())

