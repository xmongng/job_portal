"""Đơn ứng tuyển, lịch sử trạng thái và ghi chú nội bộ."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Snapshot hồ sơ nộp cho một job; khóa ghép FK đảm bảo CV thuộc đúng applicant.
class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["resume_id", "applicant_id"],
            ["resumes.id", "resumes.applicant_id"],
            name="fk_applications_resume_applicant_resumes",
        ),
        UniqueConstraint("applicant_id", "job_id", name="uq_applications_applicant_job"),
        CheckConstraint(
            "status IN ('APPLIED', 'SCREENING', 'INTERVIEW', 'OFFER', "
            "'HIRED', 'REJECTED', 'WITHDRAWN')",
            name="valid_status",
        ),
        CheckConstraint("version >= 1", name="positive_version"),
        CheckConstraint(
            "(status IN ('HIRED', 'REJECTED', 'WITHDRAWN')) = (ended_at IS NOT NULL)",
            name="terminal_has_end_time",
        ),
        Index(
            "ix_applications_job_status_created", "job_id", "status", text("created_at DESC"), "id"
        ),
        Index("ix_applications_applicant_created", "applicant_id", text("created_at DESC"), "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), nullable=False)
    resume_id: Mapped[UUID] = mapped_column(nullable=False)
    contact_name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(254), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    cover_letter: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="APPLIED")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Lịch sử chuyển trạng thái công khai; feedback và ghi chú nội bộ không nằm ở đây.
class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    __table_args__ = (
        CheckConstraint("actor_type IN ('USER', 'SYSTEM')", name="valid_actor_type"),
        CheckConstraint(
            "to_status IN ('APPLIED', 'SCREENING', 'INTERVIEW', 'OFFER', "
            "'HIRED', 'REJECTED', 'WITHDRAWN')",
            name="valid_to_status",
        ),
        Index(
            "ix_application_status_history_application_created",
            "application_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(16))
    to_status: Mapped[str] = mapped_column(String(16), nullable=False)
    changed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    actor_type: Mapped[str] = mapped_column(String(8), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# Ghi chú chỉ dành cho recruiter cùng công ty; không trả về trong applicant DTO.
class ApplicationNote(Base):
    __tablename__ = "application_notes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), nullable=False)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
