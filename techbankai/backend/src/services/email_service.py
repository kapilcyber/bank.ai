"""Email service for sending emails via SMTP."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """
    Send an email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (optional, defaults to HTML stripped)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if SMTP is configured
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        logger.warning("⚠️ SMTP not configured. Email will be logged instead of sent.")
        logger.info(f"📧 Email would be sent to: {to_email}")
        logger.info(f"📧 Subject: {subject}")
        logger.info(f"📧 Body:\n{html_body}")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
        msg['To'] = to_email
        
        # Add text and HTML parts
        if text_body:
            part1 = MIMEText(text_body, 'plain')
            msg.attach(part1)
        
        part2 = MIMEText(html_body, 'html')
        msg.attach(part2)
        
        # Connect to SMTP server
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            if settings.smtp_use_tls:
                server.starttls()
        
        # Login and send
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False


def send_password_reset_email(to_email: str, code: str) -> bool:
    """
    Send password reset verification code email.
    
    Args:
        to_email: Recipient email address
        code: 6-digit verification code
    
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = "Password Reset Verification Code - TechBank.ai"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset Code</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">TechBank.ai</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0;">
            <h2 style="color: #667eea; margin-top: 0;">Password Reset Request</h2>
            
            <p>Hello,</p>
            
            <p>We received a request to reset your password for your TechBank.ai account.</p>
            
            <div style="background: white; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 30px 0;">
                <p style="margin: 0; font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px;">Your Verification Code</p>
                <p style="margin: 10px 0 0 0; font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 5px; font-family: 'Courier New', monospace;">{code}</p>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                <strong>⚠️ Important:</strong> This code will expire in <strong>10 minutes</strong>.
            </p>
            
            <p style="color: #666; font-size: 14px;">
                If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
            </p>
            
            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; margin: 0;">
                This is an automated message from TechBank.ai. Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
TechBank.ai - Password Reset Request

Hello,

We received a request to reset your password for your TechBank.ai account.

Your Verification Code: {code}

⚠️ Important: This code will expire in 10 minutes.

If you didn't request this password reset, please ignore this email. Your password will remain unchanged.

---
This is an automated message from TechBank.ai. Please do not reply to this email.
    """
    
    return send_email(to_email, subject, html_body, text_body)

