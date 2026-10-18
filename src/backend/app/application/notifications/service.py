"""Thông báo: API chỉ gọi store trong sql/notification.sql."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import row_dict
from app.infrastructure.persistence import stores


# Đọc thông báo đúng user trong JWT, loại trường xử lý email nội bộ.
def list_notifications(db: Session, actor_id: UUID, limit: int, offset: int) -> list[dict]:
    return [
        row_dict(n, exclude=("email_error", "email_attempts", "email_sent_at"))
        for n in stores.many(
            db, "list_user_notifications", user_id=actor_id, limit=limit, offset=offset
        )
    ]


# Store cập nhật đúng chủ sở hữu; không tìm thấy thì API trả 404.
def read_notification(db: Session, actor_id: UUID, notification_id: UUID) -> dict:
    notification = stores.one(db, "mark_notification_read", id=notification_id, user_id=actor_id)
    if notification is None:
        raise HTTPException(404, "Notification not found")
    return row_dict(notification, exclude=("email_error", "email_attempts", "email_sent_at"))
