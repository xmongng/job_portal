"""Công ty và quan hệ giữa recruiter với công ty."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Hồ sơ công ty với trạng thái duyệt tối giản.
class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')",
            name="valid_verification_status",
        ),
        CheckConstraint("status IN ('ACTIVE', 'SUSPENDED')", name="valid_status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500))
    verification_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="PENDING"
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Bảng nối cho phép một công ty có nhiều recruiter và phân biệt OWNER/MEMBER.
class CompanyMembership(Base):
    __tablename__ = "company_memberships"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_company_membership"),
        UniqueConstraint("user_id", name="uq_recruiter_one_company"),
        CheckConstraint("membership_role IN ('OWNER', 'MEMBER')", name="valid_role"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    membership_role: Mapped[str] = mapped_column(String(8), nullable=False, server_default="MEMBER")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
