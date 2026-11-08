from datetime import datetime

from schemas.base import CamelCaseSchema


class NotificationResponse(CamelCaseSchema):
    id: int
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationsReadResponse(CamelCaseSchema):
    updated_count: int
