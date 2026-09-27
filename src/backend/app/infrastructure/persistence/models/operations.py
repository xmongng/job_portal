"""Thông báo, hàng đợi email, audit và giới hạn endpoint nhạy cảm."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Thông báo trong ứng dụng; event_key giúp mỗi người chỉ nhận một bản/sự kiện.
class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "event_key", name="uq_notifications_user_event"),
        CheckConstraint(
            "resource_type IS NULL OR resource_type IN "
            "('JOB', 'APPLICATION', 'INTERVIEW', 'OFFER', 'COMPANY')",
            name="valid_resource_type",
        ),
        Index("ix_notifications_user_created", "user_id", text("created_at DESC"), "id"),
        Index(
            "ix_notifications_unread",
            "user_id",
            "created_at",
            postgresql_where=text("read_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_key: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(32))
    resource_id: Mapped[UUID | None] = mapped_column()
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Email chờ worker gửi; payload mã hóa tại application layer trước khi ghi database.
class EmailDelivery(Base):
    __tablename__ = "email_deliveries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'SENT', 'FAILED')", name="valid_status"
        ),
        CheckConstraint("attempts >= 0", name="nonnegative_attempts"),
        Index("ix_email_deliveries_due", "status", "next_attempt_at"),
        Index(
            "ix_email_deliveries_processing_lease",
            "locked_until",
            postgresql_where=text("status = 'PROCESSING'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    notification_id: Mapped[UUID | None] = mapped_column(ForeignKey("notifications.id"))
    dedup_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    recipient: Mapped[str] = mapped_column(String(254), nullable=False)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Sự kiện bảo mật/nhạy cảm; metadata phải qua allowlist và không chứa secret.
class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("outcome IN ('SUCCESS', 'DENIED', 'FAILURE')", name="valid_outcome"),
        Index("ix_audit_logs_created", text("created_at DESC"), "id"),
        Index("ix_audit_logs_entity_created", "entity_type", "entity_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column()
    request_id: Mapped[UUID] = mapped_column(nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# Bộ đếm rate limit cho login/register/reset/verify; subject_hash là HMAC, không lưu IP/email thô.
class SecurityRateWindow(Base):
    __tablename__ = "security_rate_windows"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('LOGIN', 'REGISTER', 'RESET', 'VERIFY_RESEND')", name="valid_scope"
        ),
        CheckConstraint("request_count >= 0", name="nonnegative_count"),
    )

    scope: Mapped[str] = mapped_column(String(32), primary_key=True)
    subject_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
