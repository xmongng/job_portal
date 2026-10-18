"""CV: quyền và default/delete ở Python; metadata chỉ đọc/ghi qua sql/resume.sql."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_applicant, row_dict
from app.infrastructure.persistence import stores
from app.infrastructure.persistence.stores import Record


def check_applicant(db: Session, actor_id: UUID) -> UUID:
    return require_applicant(db, actor_id).id


# CV đầu tiên mặc định là default; service khóa applicant trước khi thêm metadata.
def create_resume(db: Session, actor_id: UUID, data: dict) -> dict:
    applicant = require_applicant(db, actor_id, lock=True)
    first = stores.one(db, "get_first_resume", applicant_id=applicant.id) is None
    resume = stores.one(
        db,
        "insert_resume",
        applicant_id=applicant.id,
        title=data["title"],
        storage_key=data["storage_key"],
        original_name=data["original_name"],
        mime_type="application/pdf",
        size_bytes=data["size_bytes"],
        is_default=first,
    )
    return row_dict(resume, exclude=("storage_key",))


# Liệt kê metadata chính chủ, không lộ key lưu file.
def list_resumes(db: Session, actor_id: UUID, limit: int, offset: int) -> list[dict]:
    applicant = require_applicant(db, actor_id)
    return [
        row_dict(r, exclude=("storage_key",))
        for r in stores.many(
            db, "list_applicant_resumes", applicant_id=applicant.id, limit=limit, offset=offset
        )
    ]


# Lấy CV bằng store rồi kiểm tra owner; file key chỉ dùng nội bộ backend.
def owned_resume(db: Session, actor_id: UUID, resume_id: UUID, *, lock: bool = False) -> Record:
    applicant = require_applicant(db, actor_id)
    resume = stores.one(db, "lock_resume" if lock else "get_resume_by_id", id=resume_id)
    if resume is None or resume.applicant_id != applicant.id:
        raise HTTPException(404, "Resume not found")
    return resume


def get_owned_resume(db: Session, actor_id: UUID, resume_id: UUID) -> dict:
    return row_dict(owned_resume(db, actor_id, resume_id))


# Bỏ default cũ trước khi đặt mới; cả hai store cùng một transaction.
def set_default_resume(db: Session, actor_id: UUID, resume_id: UUID) -> dict:
    applicant = require_applicant(db, actor_id, lock=True)
    owned_resume(db, actor_id, resume_id)
    stores.execute(db, "clear_default_resumes", applicant_id=applicant.id)
    updated = stores.one(db, "set_resume_default", id=resume_id, is_default=True)
    return row_dict(updated, exclude=("storage_key",))


# Chỉ xóa CV chưa dùng; nếu cần, chọn lại default trước khi commit.
def delete_resume(db: Session, actor_id: UUID, resume_id: UUID) -> dict:
    applicant = require_applicant(db, actor_id, lock=True)
    resume = owned_resume(db, actor_id, resume_id, lock=True)
    if stores.many(db, "find_resume_application", resume_id=resume_id):
        raise HTTPException(409, "Resume is attached to an application")
    stores.execute(db, "delete_resume_metadata", id=resume_id)
    if resume.is_default:
        replacement = stores.one(db, "get_first_resume", applicant_id=applicant.id)
        if replacement:
            stores.execute(db, "set_resume_default", id=replacement.id, is_default=True)
    return row_dict(resume)
