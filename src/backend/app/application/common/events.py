"""Ghi history/audit/notification qua store trong cùng transaction nghiệp vụ."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.persistence import stores


# Store nằm trong sql/notification.sql; không tự commit ở đây.
def audit(db: Session, actor_id: UUID, action: str, resource_id: UUID) -> None:
    stores.execute(
        db, "insert_audit_log", actor_id=actor_id, action=action, resource_id=resource_id
    )


# In-app notification được lưu cùng transaction; SMTP worker gửi sau commit.
def notify(
    db: Session, user_id: UUID, title: str, body: str, resource_type: str, resource_id: UUID
) -> None:
    stores.execute(
        db,
        "insert_notification",
        user_id=user_id,
        title=title,
        body=body,
        resource_type=resource_type,
        resource_id=resource_id,
    )
