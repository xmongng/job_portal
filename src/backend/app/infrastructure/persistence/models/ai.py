"""Kết quả AI đã kiểm tra và bộ đếm hạn mức AI."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Bản ghi gọi AI; chỉ lưu input hash và output đã validate, không lưu prompt thô.
class AiOperation(Base):
    __tablename__ = "ai_operations"
    __table_args__ = (
        CheckConstraint("feature IN ('MATCH_EXPLANATION', 'JD_DRAFT')", name="valid_feature"),
        CheckConstraint("status IN ('SUCCEEDED', 'FAILED')", name="valid_status"),
        CheckConstraint(
            "feature <> 'MATCH_EXPLANATION' OR (applicant_id IS NOT NULL AND job_id IS NOT NULL)",
            name="match_has_applicant_and_job",
        ),
        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0", name="nonnegative_input_tokens"
        ),
        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0", name="nonnegative_output_tokens"
        ),
        Index("ix_ai_operations_cache", "requested_by", "feature", "input_hash", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    feature: Mapped[str] = mapped_column(String(24), nullable=False)
    applicant_id: Mapped[UUID | None] = mapped_column(ForeignKey("applicants.id"))
    job_id: Mapped[UUID | None] = mapped_column(ForeignKey("jobs.id"))
    input_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(64))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# Bộ đếm hạn mức AI theo user, feature và ngày UTC; cập nhật atomically trong use case.
class AiRateWindow(Base):
    __tablename__ = "ai_rate_windows"
    __table_args__ = (
        CheckConstraint("feature IN ('MATCH_EXPLANATION', 'JD_DRAFT')", name="valid_feature"),
        CheckConstraint("request_count >= 0", name="nonnegative_count"),
        CheckConstraint("reserved_tokens >= 0", name="nonnegative_reserved_tokens"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    feature: Mapped[str] = mapped_column(String(24), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    reserved_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
