"""Hồ sơ ứng viên, học vấn, kinh nghiệm và kỹ năng."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Một hồ sơ ứng viên gắn duy nhất với một tài khoản role APPLICANT.
class Applicant(Base):
    __tablename__ = "applicants"

    __table_args__ = (
        CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="nonnegative_years_experience",
        ),
        CheckConstraint(
            "desired_salary_min IS NULL OR desired_salary_min >= 0",
            name="nonnegative_salary_min",
        ),
        CheckConstraint(
            "desired_salary_max IS NULL OR desired_salary_max >= 0",
            name="nonnegative_salary_max",
        ),
        CheckConstraint(
            "desired_salary_min IS NULL OR desired_salary_max IS NULL "
            "OR desired_salary_max >= desired_salary_min",
            name="valid_salary_range",
        ),
        CheckConstraint(
            "preferred_work_mode IS NULL OR preferred_work_mode IN ('ONSITE', 'HYBRID', 'REMOTE')",
            name="valid_work_mode",
        ),
        CheckConstraint(
            "preferred_employment_type IS NULL OR "
            "preferred_employment_type IN ('FULL_TIME', 'PART_TIME', 'INTERNSHIP', 'CONTRACT')",
            name="valid_employment_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    headline: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    location_id: Mapped[UUID | None] = mapped_column(ForeignKey("locations.id"))
    preferred_location_id: Mapped[UUID | None] = mapped_column(ForeignKey("locations.id"))
    years_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    desired_salary_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    desired_salary_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    preferred_work_mode: Mapped[str | None] = mapped_column(String(8))
    preferred_employment_type: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# Một mục học vấn thuộc về đúng một hồ sơ ứng viên.
class ApplicantEducation(Base):
    __tablename__ = "applicant_educations"

    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="valid_date_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), nullable=False)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(100))
    field_of_study: Mapped[str | None] = mapped_column(String(150))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# Một mục kinh nghiệm; tên công ty là thông tin tự khai, không liên kết bảng companies.
class ApplicantExperience(Base):
    __tablename__ = "applicant_experiences"

    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="valid_date_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# Bảng nối kỹ năng; cặp applicant_id/skill_id là khóa chính, không có ID riêng.
class ApplicantSkill(Base):
    __tablename__ = "applicant_skills"

    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
