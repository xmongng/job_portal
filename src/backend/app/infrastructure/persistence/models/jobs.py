"""Tin tuyển dụng, kỹ năng yêu cầu và lịch sử duyệt tin."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Tin tuyển dụng; thay đổi trạng thái và version phải được xử lý trong transaction.
class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'PENDING_APPROVAL', 'REJECTED', 'PUBLISHED', 'CLOSED')",
            name="valid_status",
        ),
        CheckConstraint(
            "employment_type IS NULL OR employment_type IN "
            "('FULL_TIME', 'PART_TIME', 'INTERNSHIP', 'CONTRACT')",
            name="valid_employment_type",
        ),
        CheckConstraint(
            "work_mode IS NULL OR work_mode IN ('ONSITE', 'HYBRID', 'REMOTE')",
            name="valid_work_mode",
        ),
        CheckConstraint(
            "seniority IS NULL OR seniority IN "
            "('INTERN', 'JUNIOR', 'MIDDLE', 'SENIOR', 'LEAD', 'MANAGER')",
            name="valid_seniority",
        ),
        CheckConstraint(
            "experience_min_years IS NULL OR experience_min_years >= 0",
            name="nonnegative_experience",
        ),
        CheckConstraint("vacancy_count IS NULL OR vacancy_count > 0", name="positive_vacancy"),
        CheckConstraint("salary_min IS NULL OR salary_min >= 0", name="nonnegative_salary_min"),
        CheckConstraint("salary_max IS NULL OR salary_max >= 0", name="nonnegative_salary_max"),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min",
            name="valid_salary_range",
        ),
        CheckConstraint(
            "(is_negotiable AND salary_min IS NULL AND salary_max IS NULL) OR "
            "(NOT is_negotiable AND salary_min IS NOT NULL AND salary_max IS NOT NULL)",
            name="salary_negotiability_consistency",
        ),
        CheckConstraint("currency = 'VND'", name="vnd_only"),
        CheckConstraint("salary_period = 'MONTH'", name="monthly_salary_only"),
        CheckConstraint("version >= 1", name="positive_version"),
        Index("ix_jobs_public_search", "status", "deadline", text("created_at DESC"), "id"),
        Index("ix_jobs_company_status", "company_id", "status"),
        Index("ix_jobs_category_location", "category_id", "location_id"),
        Index(
            "ix_jobs_full_text",
            text(
                "to_tsvector('simple'::regconfig, "
                "(((COALESCE(title, ''::character varying)::text || ' '::text) "
                "|| COALESCE(description, ''::text)) || ' '::text) "
                "|| COALESCE(requirements, ''::text))"
            ),
            postgresql_using="gin",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    benefits: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("job_categories.id"))
    location_id: Mapped[UUID | None] = mapped_column(ForeignKey("locations.id"))
    address: Mapped[str | None] = mapped_column(String(500))
    employment_type: Mapped[str | None] = mapped_column(String(16))
    work_mode: Mapped[str | None] = mapped_column(String(8))
    seniority: Mapped[str | None] = mapped_column(String(16))
    experience_min_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    vacancy_count: Mapped[int | None] = mapped_column(Integer)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    is_negotiable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default="VND")
    salary_period: Mapped[str] = mapped_column(String(8), nullable=False, server_default="MONTH")
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="DRAFT")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closure_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Bảng nối kỹ năng yêu cầu; khóa chính gồm job_id và skill_id.
class JobSkill(Base):
    __tablename__ = "job_skills"
    __table_args__ = (Index("ix_job_skills_skill_job", "skill_id", "job_id"),)

    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)


# Lịch sử trạng thái tin tuyển dụng; use case chỉ thêm, không sửa bản ghi cũ.
class JobStatusHistory(Base):
    __tablename__ = "job_status_history"
    __table_args__ = (
        CheckConstraint("actor_type IN ('USER', 'SYSTEM')", name="valid_actor_type"),
        CheckConstraint(
            "to_status IN ('DRAFT', 'PENDING_APPROVAL', 'REJECTED', 'PUBLISHED', 'CLOSED')",
            name="valid_to_status",
        ),
        Index("ix_job_status_history_job_created", "job_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(24))
    to_status: Mapped[str] = mapped_column(String(24), nullable=False)
    changed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(Text)
    actor_type: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
