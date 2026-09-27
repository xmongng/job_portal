"""Các vòng phỏng vấn thuộc một đơn ứng tuyển."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Một vòng phỏng vấn; kiểm tra trùng lịch cần khóa application trong use case.
class Interview(Base):
    __tablename__ = "interviews"
    __table_args__ = (
        UniqueConstraint("application_id", "round_number", name="uq_interviews_application_round"),
        CheckConstraint("round_number > 0", name="positive_round"),
        CheckConstraint("ends_at > starts_at", name="valid_time_range"),
        CheckConstraint("mode IN ('ONLINE', 'OFFLINE')", name="valid_mode"),
        CheckConstraint(
            "(mode = 'ONLINE' AND meeting_url IS NOT NULL) OR "
            "(mode = 'OFFLINE' AND address IS NOT NULL)",
            name="mode_location_required",
        ),
        CheckConstraint(
            "status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW')",
            name="valid_status",
        ),
        CheckConstraint(
            "(status = 'COMPLETED' AND result IN ('PASS', 'FAIL', 'UNDECIDED')) OR "
            "(status <> 'COMPLETED' AND result IS NULL)",
            name="result_only_when_completed",
        ),
        CheckConstraint(
            "status <> 'CANCELLED' OR cancellation_reason IS NOT NULL",
            name="cancelled_has_reason",
        ),
        CheckConstraint("version >= 1", name="positive_version"),
        Index("ix_interviews_application_status_starts", "application_id", "status", "starts_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mode: Mapped[str] = mapped_column(String(8), nullable=False)
    meeting_url: Mapped[str | None] = mapped_column(String(2048))
    address: Mapped[str | None] = mapped_column(String(500))
    interviewer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="SCHEDULED")
    result: Mapped[str | None] = mapped_column(String(16))
    feedback: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
