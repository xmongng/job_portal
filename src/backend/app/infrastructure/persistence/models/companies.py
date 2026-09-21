"""Công ty, thành viên tuyển dụng và lời mời tham gia công ty."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Hồ sơ doanh nghiệp cùng trạng thái xét duyệt và hoạt động trên nền tảng.
class Company(Base):
    __tablename__ = "companies"

    __table_args__ = (
        CheckConstraint(
            "size_band IN ('1_10', '11_50', '51_200', '201_500', '501_1000', 'ABOVE_1000')",
            name="valid_size_band",
        ),
        CheckConstraint(
            "verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')",
            name="valid_verification_status",
        ),
        CheckConstraint("status IN ('ACTIVE', 'SUSPENDED')", name="valid_status"),
        CheckConstraint(
            "verification_status <> 'REJECTED' OR verification_note IS NOT NULL",
            name="rejected_has_note",
        ),
        CheckConstraint(
            "status <> 'SUSPENDED' OR suspension_reason IS NOT NULL",
            name="suspended_has_reason",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str] = mapped_column(String(120), nullable=False)
    size_band: Mapped[str] = mapped_column(String(16), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(2048))
    logo_key: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    location_id: Mapped[UUID] = mapped_column(ForeignKey("locations.id"), nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="PENDING"
    )
    verification_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="ACTIVE")
    suspension_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# Liên kết recruiter với công ty; OWNER là vai trò trong công ty, không phải role user.
class CompanyMembership(Base):
    __tablename__ = "company_memberships"

    __table_args__ = (
        CheckConstraint("membership_role IN ('OWNER', 'MEMBER')", name="valid_membership_role"),
        Index(
            "uq_company_memberships_active_user",
            "user_id",
            unique=True,
            postgresql_where=text("left_at IS NULL"),
        ),
        Index(
            "uq_company_memberships_active_owner",
            "company_id",
            unique=True,
            postgresql_where=text("membership_role = 'OWNER' AND left_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    membership_role: Mapped[str] = mapped_column(String(8), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# Lời mời recruiter; chỉ lưu digest của token và tối đa một lời mời đang chờ/email/công ty.
class CompanyInvitation(Base):
    __tablename__ = "company_invitations"

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED')",
            name="valid_status",
        ),
        CheckConstraint(
            "(accepted_by IS NULL) = (accepted_at IS NULL)",
            name="acceptance_fields_together",
        ),
        Index(
            "uq_company_invitations_pending_email",
            "company_id",
            "email",
            unique=True,
            postgresql_where=text("status = 'PENDING'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    invited_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="PENDING")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
