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

    def fetch_unread_emails(self, max_count: int = 50) -> List[Dict[str, Any]]:
        headers = self.authenticator.get_auth_headers()
        url = self._build_inbox_url()
        params = {
            "$filter": "isRead eq false and hasAttachments eq true",
            "$select": "id,subject,from,receivedDateTime,hasAttachments",
            "$top": min(max_count, 25)
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get("value", [])
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise

    def filter_resume_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [e for e in emails if self._contains_resume_keywords(e.get("subject", ""))]

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
    VALID_EXTENSIONS = {".pdf", ".docx"}
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

    def fetch_emails_to_process(self, max_emails: int = 50) -> List[Dict[str, Any]]:
        unread = self.email_fetcher.fetch_unread_emails(max_emails)
        return self.email_fetcher.filter_resume_emails(unread)

    def get_email_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        return self.attachment_handler.get_valid_resume_attachments(message_id)

    def mark_processed(self, message_id: str):
        self.email_fetcher.mark_as_read(message_id)

