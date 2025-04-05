"""
Email notification service for meeting recordings.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from pathlib import Path

from config.config import get_settings
from src.utils import get_logger, format_structured_log
from src.utils.exceptions import BaseAppException, ErrorCode
from src.enums.notification import NotificationStatus, NotificationChannel
from src.services.notification.constants import DEFAULT_EMAIL_SUBJECT, MAX_RETRY_ATTEMPTS
from src.services.notification.templates import get_template


logger = get_logger(__name__)

class EmailSendError(BaseAppException):
    """Exception raised when sending an email fails."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=ErrorCode.API_ERROR,
            details=details,
            original_exception=original_exception
        )


class EmailNotifier:
    """
    Email notification service for meeting recordings.
    """
    
    def __init__(
        self, 
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        recipient_emails: Optional[str] = None
    ):
        """
        Initialize the email notifier.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            sender_email: Email address to send from
            sender_password: Password for the sender email
            recipient_emails: Comma-separated list of recipient emails
        """
        settings = get_settings()
        
        self.smtp_server = smtp_server or settings.SMTP_SERVER
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.sender_email = sender_email or settings.SENDER_EMAIL
        self.sender_password = sender_password or settings.SENDER_PASSWORD
        
        # Parse recipient emails
        if recipient_emails:
            self.recipient_emails = [e.strip() for e in recipient_emails.split(',')]
        elif settings.RECIPIENT_EMAILS:
            self.recipient_emails = [e.strip() for e in settings.RECIPIENT_EMAILS.split(',')]
        else:
            self.recipient_emails = []
        
        logger.info(
            format_structured_log(
                "EmailNotifier initialized",
                {
                    "smtp_server": self.smtp_server,
                    "smtp_port": self.smtp_port,
                    "sender_email": self.sender_email,
                    "recipients": len(self.recipient_emails)
                }
            )
        )
    
    async def send_meeting_notification(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email notification about a new meeting.
        
        Args:
            meeting_data: Meeting data to include in the notification
            
        Returns:
            Status dictionary with information about the notification
        """
        notification_id = f"email_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            "notification_id": notification_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notification_type": NotificationChannel.EMAIL.value,
            "status": NotificationStatus.PENDING.value
        }
        
        # Validate required settings
        if not self.recipient_emails:
            logger.warning("No recipient emails configured, skipping notification")
            result["status"] = NotificationStatus.SKIPPED.value
            result["message"] = "No recipient emails configured"
            return result
        
        if not self.smtp_server or not self.sender_email or not self.sender_password:
            logger.warning("Email configuration incomplete, skipping notification")
            result["status"] = NotificationStatus.SKIPPED.value
            result["message"] = "Email configuration incomplete"
            return result
        
        # Extract meeting details
        customer = meeting_data.get("customer_name", "Unknown Client")
        meeting_date = meeting_data.get("meeting_date", "Unknown Date")
        
        # Create email subject using the constant
        subject = DEFAULT_EMAIL_SUBJECT.replace("[TimeLogger]", "[TEST]")
        if customer and meeting_date:
            subject = f"{subject}: {customer} on {meeting_date}"
        
        # Create the email content
        message = self._create_email_message(subject, meeting_data)
        
        # asyncio to send email without blocking
        retry_count = 0
        while retry_count < MAX_RETRY_ATTEMPTS:
            try:
                await asyncio.to_thread(
                    self._send_email,
                    message
                )
                
                logger.info(
                    format_structured_log(
                        f"Email notification sent [{notification_id}]",
                        {
                            "recipients": len(self.recipient_emails),
                            "customer": customer
                        }
                    )
                )
                
                result["status"] = NotificationStatus.SENT.value
                result["recipients"] = len(self.recipient_emails)
                return result
                
            except Exception as e:
                retry_count += 1
                if retry_count >= MAX_RETRY_ATTEMPTS:
                    logger.error(
                        format_structured_log(
                            f"Failed to send email notification after {MAX_RETRY_ATTEMPTS} attempts [{notification_id}]",
                            {"error": str(e)}
                        ),
                        exc_info=True
                    )
                    
                    result["status"] = NotificationStatus.FAILED.value
                    result["error"] = str(e)
                    return result
                else:
                    logger.warning(
                        f"Email send attempt {retry_count} failed, retrying: {str(e)}"
                    )
                    await asyncio.sleep(1)  # Wait before retrying
        
        return result
    
    def _create_email_message(self, subject: str, meeting_data: Dict[str, Any]) -> MIMEMultipart:
        """
        Create an email message with meeting data.
        
        Args:
            subject: Email subject line
            meeting_data: Meeting data to include in the body
            
        Returns:
            MIMEMultipart message object
        """
        try:
            # Get the template using the centralized template system
            template = get_template("meeting_notification")
            
            # Prepare data with defaults for missing values
            formatted_data = {
                "customer_name": meeting_data.get('customer_name', 'Not provided'),
                "meeting_date": meeting_data.get('meeting_date', 'Not provided'),
                "start_time": meeting_data.get('start_time', 'Not provided'),
                "end_time": meeting_data.get('end_time', 'Not provided'),
                "total_hours": meeting_data.get('total_hours', 'Not provided'),
                "notes": meeting_data.get('notes', 'No notes provided')
            }
            
            # Format the template with the data
            body = template.format(**formatted_data)
            
        except Exception as e:
            logger.error(f"Template formatting error: {str(e)}", exc_info=True)
            # Use a very simple fallback for catastrophic failures
            body = f"""
            <html><body>
                <h2>Meeting Data</h2>
                <p>Customer: {meeting_data.get('customer_name', 'Not provided')}</p>
                <p>Date: {meeting_data.get('meeting_date', 'Not provided')}</p>
                <p>Hours: {meeting_data.get('total_hours', 'Not provided')}</p>
            </body></html>
            """
        
        # Create the email message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = ", ".join(self.recipient_emails)
        
        # Attach HTML content
        html_part = MIMEText(body, "html")
        message.attach(html_part)
        
        return message
    
    def _send_email(self, message: MIMEMultipart) -> None:
        """
        Send an email using SMTP.
        This is a blocking operation that should be run in a thread.
        
        Args:
            message: MIMEMultipart message to send
            
        Raises:
            EmailSendError: If sending the email fails
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
        except Exception as e:
            raise EmailSendError(
                f"Failed to send email: {str(e)}",
                details={"smtp_server": self.smtp_server, "smtp_port": self.smtp_port},
                original_exception=e
            )