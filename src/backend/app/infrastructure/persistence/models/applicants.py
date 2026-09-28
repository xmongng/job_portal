"""Hồ sơ ứng viên và kỹ năng."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Học vấn và kinh nghiệm được gộp thành JSON để giảm số bảng cho dự án học tập.
class Applicant(Base):
    __tablename__ = "applicants"
    __table_args__ = (
        CheckConstraint("desired_salary IS NULL OR desired_salary >= 0", name="nonnegative_salary"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    headline: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(150))
    education: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    experience: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    desired_salary: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Bảng nối nhiều-nhiều giữa hồ sơ ứng viên và kỹ năng.
class ApplicantSkill(Base):
    __tablename__ = "applicant_skills"

    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
