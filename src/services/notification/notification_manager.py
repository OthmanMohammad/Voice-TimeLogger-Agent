"""
Notification manager for sending alerts about new meetings.
"""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from config.config import get_settings
from src.utils import get_logger, log_async_function_call, format_structured_log

logger = get_logger(__name__)

class NotificationManager:
    """
    Manager for sending notifications about new meetings.
    Supports multiple notification channels simultaneously.
    """
    
    def __init__(self):
        """Initialize the notification manager."""
        # Generate unique ID for this manager instance
        self.instance_id = str(uuid.uuid4())[:8]
        logger.info(f"Initializing NotificationManager instance {self.instance_id}")
        
        settings = get_settings()
        
        # Check which notification types are enabled
        self.email_enabled = settings.ENABLE_EMAIL_NOTIFICATIONS
        self.slack_enabled = settings.ENABLE_SLACK_NOTIFICATIONS
        
        # Lazy-load notification implementations when needed
        self._email_notifier = None
        self._slack_notifier = None
        
        logger.info(
            format_structured_log(
                "NotificationManager initialized",
                {
                    "instance_id": self.instance_id,
                    "email_enabled": self.email_enabled,
                    "slack_enabled": self.slack_enabled
                }
            )
        )
    
    @log_async_function_call(logger)
    async def send_notification(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notifications about a new meeting using all enabled channels.
        
        Args:
            meeting_data: Meeting data to include in the notification
            
        Returns:
            Status dictionary with information about all notifications
        """
        notification_id = f"notify_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            "notification_id": notification_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "channels": [],
            "overall_status": "skipped"
        }
        
        # Collect results from all notification attempts
        notifications_sent = False
        notification_results = []
        
        # Send email notification if enabled
        if self.email_enabled:
            email_result = await self._send_email_notification(meeting_data)
            notification_results.append(email_result)
            if email_result.get("status") == "sent":
                notifications_sent = True
            
            # Add channel info to result
            result["channels"].append({
                "type": "email",
                "status": email_result.get("status"),
                "details": email_result
            })
        
        # Send Slack notification if enabled
        if self.slack_enabled:
            slack_result = await self._send_slack_notification(meeting_data)
            notification_results.append(slack_result)
            if slack_result.get("status") == "sent":
                notifications_sent = True
            
            # Add channel info to result
            result["channels"].append({
                "type": "slack",
                "status": slack_result.get("status"),
                "details": slack_result
            })
        
        # Determine overall status
        if notifications_sent:
            result["overall_status"] = "sent"
        elif result["channels"]:
            result["overall_status"] = "partial"
        else:
            result["overall_status"] = "skipped"
            result["message"] = "No notification channels enabled"
        
        return result
    
    async def _send_email_notification(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an email notification.
        
        Args:
            meeting_data: Meeting data to include in the notification
            
        Returns:
            Status dictionary
        """
        # Lazy-load the email notifier
        if not self._email_notifier:
            from src.services.notification.email_notifier import EmailNotifier
            self._email_notifier = EmailNotifier()
        
        return await self._email_notifier.send_meeting_notification(meeting_data)
    
    async def _send_slack_notification(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a Slack notification.
        
        Args:
            meeting_data: Meeting data to include in the notification
            
        Returns:
            Status dictionary
        """
        # Lazy-load the slack notifier
        if not self._slack_notifier:
            from src.services.notification.slack_notifier import SlackNotifier
            self._slack_notifier = SlackNotifier()
        
        return await self._slack_notifier.send_meeting_notification(meeting_data)