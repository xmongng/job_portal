"""Các vòng phỏng vấn của một đơn ứng tuyển."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Mỗi application có thể có nhiều vòng, phân biệt bằng round_number.
class Interview(Base):
    __tablename__ = "interviews"
    __table_args__ = (
        UniqueConstraint("application_id", "round_number", name="uq_application_round"),
        CheckConstraint("round_number > 0", name="positive_round"),
        CheckConstraint("mode IN ('ONLINE', 'OFFLINE')", name="valid_mode"),
        CheckConstraint("status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')", name="valid_status"),
        CheckConstraint("result IS NULL OR result IN ('PASS', 'FAIL')", name="valid_result"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mode: Mapped[str] = mapped_column(String(8), nullable=False)
    location_or_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="SCHEDULED")
    result: Mapped[str | None] = mapped_column(String(8))
    feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
