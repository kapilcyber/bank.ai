"""Storage service with Google Drive and local fallback support."""
import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from src.utils.validators import sanitize_filename, validate_file_size
from src.utils.logger import get_logger
from src.services.google_drive import upload_file_to_gdrive
from src.config.settings import settings

logger = get_logger(__name__)

# Use settings for upload configuration
UPLOAD_DIR = settings.upload_dir
MAX_FILE_SIZE_MB = settings.max_file_size_mb


class StorageService:
    """Unified storage service with Google Drive, PostgreSQL, and local fallback."""
    
    @staticmethod
    async def upload(file: UploadFile, subfolder: str = "resumes", save_to_db: bool = True) -> tuple[str, str, bytes, str]:
        """
        Upload file to storage.
        Returns: (file_id_or_path, file_url, file_content, mime_type)
        - If save_to_db=True: file_id_or_path is placeholder, file_url is API endpoint, file_content is bytes, mime_type is MIME type
        - If save_to_db=False: file_id_or_path is file_path, file_url is static file URL, file_content is bytes, mime_type is MIME type
        """
        # Read file content
        content = await file.read()
        
        # Validate file size
        if not validate_file_size(len(content), MAX_FILE_SIZE_MB):
            raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit")
            
        # Validate file signature (Magic Numbers)
        from src.utils.validators import validate_file_signature
        file_extension = file.filename.split('.')[-1].lower()
        if not validate_file_signature(content, file_extension):
            logger.warning(f"Security Rejection: File signature mismatch for {file.filename}")
            raise ValueError(f"Invalid file content: The file does not appear to be a valid {file_extension.upper()} file.")
        
        # Determine MIME type
        mime_type = file.content_type or _get_mime_type(file_extension)
        
        # If save_to_db is True, return content for database storage
        if save_to_db:
            # Generate a placeholder ID (will be replaced with resume_id after save)
            file_id = str(uuid.uuid4())
            # Return API endpoint URL (will be updated with actual resume_id after save)
            file_url = f"/api/resumes/{file_id}/file"
            return file_id, file_url, content, mime_type
        
        # Try Google Drive first if enabled
        if settings.use_google_drive:
            try:
                original_filename = sanitize_filename(file.filename)
                file_id, web_view_link = await upload_file_to_gdrive(
                    content,
                    original_filename
                )
                logger.info(f"Uploaded to Google Drive: {web_view_link}")
                return file_id, web_view_link, content, mime_type
            except Exception as e:
                logger.warning(f"Google Drive upload failed, falling back to local: {e}")
        
        # Fallback to local storage
        file_path, file_url = await StorageService._save_local(file, content, subfolder)
        return file_path, file_url, content, mime_type
    
    @staticmethod
    async def _save_local(file: UploadFile, content: bytes, subfolder: str) -> tuple[str, str]:
        """Save file to local disk."""
        try:
            # Create upload directory if it doesn't exist
            upload_path = Path(UPLOAD_DIR) / subfolder
            upload_path.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            original_filename = sanitize_filename(file.filename)
            file_extension = original_filename.split('.')[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = upload_path / unique_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Generate file URL (relative path)
            file_url = f"/{UPLOAD_DIR}/{subfolder}/{unique_filename}"
            
            logger.info(f"Saved file locally: {file_path}")
            return str(file_path), file_url
        
        except Exception as e:
            logger.error(f"Failed to save file locally: {e}")
            raise


def _get_mime_type(extension: str) -> str:
    """Get MIME type from file extension."""
    mime_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
    }
    return mime_types.get(extension.lower(), 'application/octet-stream')


# Backward compatibility function
async def save_uploaded_file(file: UploadFile, subfolder: str = "resumes", save_to_db: bool = True) -> tuple[str, str, bytes, str]:
    """Save uploaded file (uses StorageService). Returns (file_id_or_path, file_url, file_content, mime_type)."""
    return await StorageService.upload(file, subfolder, save_to_db)


def delete_file(file_path: str) -> bool:
    """Delete file from disk."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        return False

