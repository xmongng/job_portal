"""Các lần phát hành offer nối tiếp cho cùng đơn ứng tuyển."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Offer mới tăng sequence_number; tối đa một DRAFT/SENT và một ACCEPTED mỗi application.
class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint(
            "application_id", "sequence_number", name="uq_offers_application_sequence"
        ),
        CheckConstraint("sequence_number > 0", name="positive_sequence"),
        CheckConstraint("salary > 0", name="positive_salary"),
        CheckConstraint("currency = 'VND'", name="vnd_only"),
        CheckConstraint(
            "status IN ('DRAFT', 'SENT', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXPIRED')",
            name="valid_status",
        ),
        CheckConstraint("version >= 1", name="positive_version"),
        CheckConstraint(
            "status NOT IN ('SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED') OR sent_at IS NOT NULL",
            name="sent_time_required",
        ),
        CheckConstraint(
            "status NOT IN ('ACCEPTED', 'REJECTED') OR responded_at IS NOT NULL",
            name="response_time_required",
        ),
        CheckConstraint(
            "status <> 'WITHDRAWN' OR (withdrawn_at IS NOT NULL AND withdrawal_reason IS NOT NULL)",
            name="withdrawal_details_required",
        ),
        Index(
            "uq_offers_active_application",
            "application_id",
            unique=True,
            postgresql_where=text("status IN ('DRAFT', 'SENT')"),
        ),
        Index(
            "uq_offers_accepted_application",
            "application_id",
            unique=True,
            postgresql_where=text("status = 'ACCEPTED'"),
        ),
        Index("ix_offers_application_status", "application_id", "status"),
        Index("ix_offers_status_deadline", "status", "response_deadline"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default="VND")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    response_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    terms: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="DRAFT")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_note: Mapped[str | None] = mapped_column(Text)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawal_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
