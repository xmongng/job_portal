"""Bản soạn CV và các file CV bất biến được lưu trong private storage."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


# Bản CV đang soạn; content cần được validate theo schema CV_V1 ở application layer.
class CvDocument(Base):
    __tablename__ = "cv_documents"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="positive_revision"),
        CheckConstraint("template_code = 'BASIC_V1'", name="valid_template"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    template_code: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Metadata của file CV; nội dung thật nằm ngoài database, không được ghi đè sau khi tạo.
class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (
        CheckConstraint("source IN ('UPLOAD', 'GENERATED')", name="valid_source"),
        CheckConstraint(
            "(source = 'GENERATED' AND cv_document_id IS NOT NULL "
            "AND document_revision IS NOT NULL) OR "
            "(source = 'UPLOAD' AND cv_document_id IS NULL "
            "AND document_revision IS NULL)",
            name="source_document_consistency",
        ),
        CheckConstraint(
            "document_revision IS NULL OR document_revision >= 1", name="positive_revision"
        ),
        CheckConstraint("size_bytes > 0 AND size_bytes <= 5242880", name="valid_size"),
        CheckConstraint("deleted_at IS NULL OR NOT is_default", name="deleted_not_default"),
        UniqueConstraint("id", "applicant_id", name="uq_resumes_id_applicant_id"),
        Index(
            "uq_resumes_active_default",
            "applicant_id",
            unique=True,
            postgresql_where=text("is_default AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    cv_document_id: Mapped[UUID | None] = mapped_column(ForeignKey("cv_documents.id"))
    document_revision: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
