from enum import Enum

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"

class NotificationChannel(Enum):
    EMAIL = "email" 
    SLACK = "slack"