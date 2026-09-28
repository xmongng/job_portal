"""Tin tuyển dụng và kỹ năng yêu cầu."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Tin tuyển dụng giữ những trường cần cho CRUD, tìm kiếm và ứng tuyển.
class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'CLOSED')", name="valid_status"),
        CheckConstraint(
            "employment_type IN ('FULL_TIME', 'PART_TIME', 'INTERNSHIP', 'CONTRACT')",
            name="valid_employment_type",
        ),
        CheckConstraint("salary_min IS NULL OR salary_min >= 0", name="nonnegative_salary_min"),
        CheckConstraint(
            "salary_max IS NULL OR salary_max >= salary_min", name="valid_salary_range"
        ),
        Index("ix_jobs_public", "status", "deadline"),
        Index("ix_jobs_company", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(16), nullable=False)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Bảng nối nhiều-nhiều giữa job và kỹ năng yêu cầu.
class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
