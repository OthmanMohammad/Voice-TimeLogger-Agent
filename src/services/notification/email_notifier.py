
"""
Email notification service for meeting recordings.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from config.config import get_settings
from src.utils import get_logger, format_structured_log
from src.utils.exceptions import BaseAppException, ErrorCode

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
            "notification_type": "email",
            "status": "pending"
        }
        
        # Validate required settings
        if not self.recipient_emails:
            logger.warning("No recipient emails configured, skipping notification")
            result["status"] = "skipped"
            result["message"] = "No recipient emails configured"
            return result
        
        if not self.smtp_server or not self.sender_email or not self.sender_password:
            logger.warning("Email configuration incomplete, skipping notification")
            result["status"] = "skipped"
            result["message"] = "Email configuration incomplete"
            return result
        
        # Extract meeting details
        customer = meeting_data.get("customer_name", "Unknown Client")
        meeting_date = meeting_data.get("meeting_date", "Unknown Date")
        
        # Create email subject and body
        subject = f"[TEST] New Meeting Log: {customer} on {meeting_date}"
        
        # Create the email content
        message = self._create_email_message(subject, meeting_data)
        
        # asyncio to send email without blocking
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
            
            result["status"] = "sent"
            result["recipients"] = len(self.recipient_emails)
            
        except Exception as e:
            logger.error(
                format_structured_log(
                    f"Failed to send email notification [{notification_id}]",
                    {"error": str(e)}
                ),
                exc_info=True
            )
            
            result["status"] = "failed"
            result["error"] = str(e)
        
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
        # Format the email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-bottom: 3px solid #007bff;">
                <h2 style="color: #007bff; margin: 0;">New Meeting Logged</h2>
            </div>
            <div style="padding: 20px;">
                <p>A new meeting has been processed and logged to Google Sheets:</p>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <th style="text-align: left; padding: 8px; background-color: #f2f2f2; border: 1px solid #ddd;">Field</th>
                        <th style="text-align: left; padding: 8px; background-color: #f2f2f2; border: 1px solid #ddd;">Value</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Customer:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{meeting_data.get('customer_name', 'Not provided')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Meeting Date:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{meeting_data.get('meeting_date', 'Not provided')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Start Time:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{meeting_data.get('start_time', 'Not provided')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>End Time:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{meeting_data.get('end_time', 'Not provided')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Total Hours:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{meeting_data.get('total_hours', 'Not provided')}</td>
                    </tr>
                </table>
                
                <div style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #6c757d; margin-bottom: 20px;">
                    <h3 style="margin-top: 0;">Notes:</h3>
                    <p>{meeting_data.get('notes', 'No notes provided')}</p>
                </div>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #6c757d; font-size: 12px;">This is an automated notification from Voice-TimeLogger-Agent.</p>
            </div>
        </body>
        </html>
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