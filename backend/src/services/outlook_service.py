"""
Outlook Service for fetching and processing resumes from Microsoft Graph API.
Adapted from the provided resume_fetcher logic.
"""
import os
import re
import base64
import logging
from typing import List, Dict, Any, Optional
import requests
from msal import ConfidentialClientApplication
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class GraphAuthenticator:
    """Handles Microsoft Graph API authentication using client credentials flow."""
    GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]

    def __init__(self):
        self.tenant_id = settings.azure_tenant_id
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            logger.error("Microsoft Graph API credentials are not fully configured in settings.")
            
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self._app: Optional[ConfidentialClientApplication] = None

    def _get_app(self) -> ConfidentialClientApplication:
        if self._app is None:
            self._app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
        return self._app

    def get_access_token(self) -> str:
        app = self._get_app()
        result = app.acquire_token_silent(scopes=self.GRAPH_SCOPE, account=None)
        if result and "access_token" in result:
            return result["access_token"]

        result = app.acquire_token_for_client(scopes=self.GRAPH_SCOPE)
        if "access_token" in result:
            return result["access_token"]

        error_description = result.get("error_description", "Unknown error")
        error_code = result.get("error", "unknown")
        raise RuntimeError(f"Failed to acquire access token: {error_code} - {error_description}")

    def get_auth_headers(self) -> dict:
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

class EmailFetcher:
    """Fetches and filters emails from Microsoft Graph API."""
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    RESUME_KEYWORDS = ["resume", "cv", "application", "job application", "profile"]

    def __init__(self, authenticator: GraphAuthenticator):
        self.authenticator = authenticator
        self.mailbox_email = settings.mailbox_email

    def _build_inbox_url(self) -> str:
        return f"{self.GRAPH_BASE_URL}/users/{self.mailbox_email}/mailFolders/inbox/messages"

    def _build_message_url(self, message_id: str) -> str:
        return f"{self.GRAPH_BASE_URL}/users/{self.mailbox_email}/messages/{message_id}"

    def _contains_resume_keywords(self, subject: str) -> bool:
        if not subject: return False
        subject_lower = subject.lower()
        for keyword in self.RESUME_KEYWORDS:
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, subject_lower):
                return True
        return False

    def fetch_unread_emails(self, max_count: int = 100, include_read: bool = False, require_keywords: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch emails from Outlook inbox with pagination support.
        
        Args:
            max_count: Maximum number of emails to fetch (default 100)
            include_read: If True, also fetch read emails (default False)
            require_keywords: If True, only fetch emails with resume keywords in subject (default False)
        """
        headers = self.authenticator.get_auth_headers()
        url = self._build_inbox_url()
        
        # Build filter based on parameters
        filter_parts = ["hasAttachments eq true"]
        if not include_read:
            filter_parts.append("isRead eq false")
        
        params = {
            "$filter": " and ".join(filter_parts),
            "$select": "id,subject,from,receivedDateTime,hasAttachments,isRead",
            "$top": min(max_count, 100)  # Microsoft Graph API max is 100 per request
        }
        
        all_emails = []
        try:
            while len(all_emails) < max_count:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                emails = data.get("value", [])
                
                if not emails:
                    break
                
                # Apply keyword filter if required
                if require_keywords:
                    emails = [e for e in emails if self._contains_resume_keywords(e.get("subject", ""))]
                
                all_emails.extend(emails)
                
                # Check for next page
                next_link = data.get("@odata.nextLink")
                if not next_link or len(all_emails) >= max_count:
                    break
                
                url = next_link
                params = {}  # Next link already has all params
            
            return all_emails[:max_count]  # Return up to max_count
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise

    def filter_resume_emails(self, emails: List[Dict[str, Any]], require_keywords: bool = False) -> List[Dict[str, Any]]:
        """Filter emails by resume keywords if required."""
        if require_keywords:
            return [e for e in emails if self._contains_resume_keywords(e.get("subject", ""))]
        return emails

    def mark_as_read(self, message_id: str) -> bool:
        headers = self.authenticator.get_auth_headers()
        url = self._build_message_url(message_id)
        try:
            response = requests.patch(url, headers=headers, json={"isRead": True}, timeout=30)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            return False

class AttachmentHandler:
    """Handles downloading and validating email attachments."""
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    # Accept common resume formats from Outlook.
    # Note: `.doc` (legacy Word) support depends on having a conversion tool available server-side
    # (e.g., MS Word via COM on Windows, LibreOffice, or antiword). See file_processor.extract_text_from_doc.
    VALID_EXTENSIONS = {".pdf", ".docx", ".doc"}
    EXCLUDED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/gif", "image/bmp", "image/webp", "image/svg+xml"}

    def __init__(self, authenticator: GraphAuthenticator):
        self.authenticator = authenticator
        self.mailbox_email = settings.mailbox_email

    def _build_attachments_url(self, message_id: str) -> str:
        return f"{self.GRAPH_BASE_URL}/users/{self.mailbox_email}/messages/{message_id}/attachments"

    def get_valid_resume_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        headers = self.authenticator.get_auth_headers()
        url = self._build_attachments_url(message_id)
        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            attachments = response.json().get("value", [])
            
            valid = []
            for att in attachments:
                if att.get("@odata.type") != "#microsoft.graph.fileAttachment": continue
                if att.get("isInline", False): continue
                if att.get("contentType", "").lower() in self.EXCLUDED_CONTENT_TYPES: continue
                
                name = att.get("name", "")
                ext = os.path.splitext(name)[1].lower()
                if ext not in self.VALID_EXTENSIONS: continue
                
                content_bytes = att.get("contentBytes")
                if content_bytes:
                    valid.append({
                        "id": att.get("id"),
                        "name": name,
                        "content_type": att.get("contentType"),
                        "content": base64.b64decode(content_bytes),
                        "extension": ext[1:] # pdf or docx
                    })
            return valid
        except Exception as e:
            logger.error(f"Error fetching attachments: {e}")
            raise

class OutlookService:
    """Main service to orchestrate Outlook resume fetching."""
    def __init__(self):
        self.authenticator = GraphAuthenticator()
        self.email_fetcher = EmailFetcher(self.authenticator)
        self.attachment_handler = AttachmentHandler(self.authenticator)

    def fetch_emails_to_process(self, max_emails: int = 100, include_read: bool = False, require_keywords: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch emails to process.
        
        Args:
            max_emails: Maximum number of emails to fetch (default 100)
            include_read: If True, also process read emails (default False)
            require_keywords: If True, only process emails with resume keywords (default False)
        """
        unread = self.email_fetcher.fetch_unread_emails(max_emails, include_read, require_keywords)
        return self.email_fetcher.filter_resume_emails(unread, require_keywords)

    def get_email_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        return self.attachment_handler.get_valid_resume_attachments(message_id)

    def mark_processed(self, message_id: str):
        self.email_fetcher.mark_as_read(message_id)

