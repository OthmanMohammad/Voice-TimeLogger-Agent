# Notification System

This document describes the notification system used to alert users about processed meeting recordings.

## Overview

The system follows a modular architecture with a manager-worker pattern. When meeting data is successfully stored, notifications can be sent through different channels (currently email, with Slack support planned).

## Architecture

### Key Components

- **NotificationManager**: Coordinates the notifications process and determines which channels to use
- **EmailNotifier**: Handles email delivery via SMTP
- **SlackNotifier**: Placeholder for Slack integration (not fully implemented)

### Support Modules

- **Enums**: Defines status codes and channel types
- **Templates**: Manages HTML email templates with caching and fallback options
- **Constants**: Stores configuration values

## Using the System

### Code Example

```python
from src.services.notification import NotificationManager

# Create notification manager
notification_manager = NotificationManager()

# Example meeting data
meeting_data = {
    "customer_name": "Acme Corp",
    "meeting_date": "2025-04-06",
    "start_time": "10:00 AM",
    "end_time": "11:30 AM",
    "total_hours": 1.5,
    "notes": "Discussed project requirements"
}

# Send notifications
result = await notification_manager.send_notification(meeting_data)

# Check result
if result["overall_status"] == "sent":
    print("Notification sent successfully")
else:
    print(f"Status: {result['overall_status']}")
    print(f"Message: {result.get('message', '')}")
```

### API Usage

Control notifications when uploading recordings:

```
POST /api/v1/speech/upload
```

Form parameters:
- `file`: Audio file (required)
- `customer_hint`: Hint about customer name (optional)
- `meeting_date_hint`: Hint about meeting date (optional)
- `notify`: Control notifications for this request (optional boolean)

When `notify` is absent, the system uses the `NOTIFICATIONS_DEFAULT` value from your environment settings.

Examples with curl:
```bash
# Enable notifications for this request
curl -X POST "http://localhost:8000/api/v1/speech/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@recording.mp3" \
  -F "notify=true"

# Disable notifications for this request
curl -X POST "http://localhost:8000/api/v1/speech/upload" \
  -F "file=@recording.mp3" \
  -F "notify=false"
```

## Configuration

### Environment Variables

Control system behavior with these environment variables:

**Basic settings:**
- `ENABLE_EMAIL_NOTIFICATIONS`: Turn email notifications on/off
- `ENABLE_SLACK_NOTIFICATIONS`: Turn Slack notifications on/off
- `NOTIFICATIONS_DEFAULT`: Default behavior when not specified in API calls

**Email settings:**
- `SMTP_SERVER`: Email server address
- `SMTP_PORT`: Email server port (usually 587)
- `SENDER_EMAIL`: From address
- `SENDER_PASSWORD`: Authentication credential
- `RECIPIENT_EMAILS`: Where to send notifications (comma-separated)

**Slack settings:**
- `SLACK_WEBHOOK_URL`: Webhook URL for your Slack workspace

## Response Format

The system returns structured data about notification attempts:

```json
{
  "notification_id": "notify_20250406123456",
  "timestamp": "2025-04-06 12:34:56",
  "channels": [
    {
      "type": "email",
      "status": "sent",
      "details": {
        "notification_id": "email_20250406123456",
        "timestamp": "2025-04-06 12:34:56",
        "notification_type": "email",
        "status": "sent",
        "recipients": 1
      }
    }
  ],
  "overall_status": "sent"
}
```

## Status Codes

Notification operations return these status values:

- `pending`: Process started but not complete
- `sent`: Notification successfully delivered
- `failed`: Delivery failed after retries
- `skipped`: Notification skipped due to configuration
- `partial`: Some channels succeeded, others failed

## Extending the System

### Adding Email Templates

Email templates are stored in `src/services/notification/templates/`:

1. Create an HTML file in this directory (e.g., `reminder_notification.html`)
2. Add a fallback version in `templates.py` under `FALLBACK_TEMPLATES`
3. Use it with `get_template("reminder_notification")`

### Supporting New Channels

To add another notification channel:

1. Create a notifier class (e.g., `TelegramNotifier`)
2. Add the channel type to `NotificationChannel` enum
3. Add a property and method in `NotificationManager`
4. Update settings validation in `config.py`

## Reliability Features

The system includes several reliability mechanisms:

- Independent channel processing prevents cascading failures
- Template system includes fallbacks if files aren't found
- Configurable retry settings for delivery attempts
- Core application flow continues even if notifications fail

## Development Notes

### Slack Integration

The `SlackNotifier` currently exists as a minimal implementation. To complete it:

1. Implement Slack message formatting with Block Kit
2. Add HTTP handling for the webhook requests
3. Handle API responses and error codes
4. Update the status reporting

The current placeholder returns `not_implemented` status:

```python
# From src/services/notification/slack_notifier.py
result["status"] = "not_implemented"
result["message"] = "Slack notifications not fully implemented yet"
```