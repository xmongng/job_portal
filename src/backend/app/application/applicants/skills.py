"""Chọn skills: Python kiểm tra quyền, store thực hiện toàn bộ đọc/ghi."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_applicant, require_role, row_dict
from app.infrastructure.persistence import stores


# Danh mục skills public, có phân trang.
def list_skills(db: Session, limit: int, offset: int) -> list[dict]:
    return [row_dict(s) for s in stores.many(db, "list_skills", limit=limit, offset=offset)]


# Admin thêm một skill vào danh mục.
def create_skill(db: Session, actor_id: UUID, name: str) -> dict:
    require_role(db, actor_id, "ADMIN")
    return row_dict(stores.one(db, "insert_skill", name=name))


# Đọc skills của applicant chính chủ.
def get_applicant_skills(db: Session, actor_id: UUID) -> list[dict]:
    applicant = require_applicant(db, actor_id)
    return [row_dict(s) for s in stores.many(db, "get_applicant_skills", applicant_id=applicant.id)]


# Thay danh sách sau khi đã kiểm tra mọi ID và khóa hồ sơ applicant.
def set_applicant_skills(db: Session, actor_id: UUID, skills: list[UUID]) -> list[dict]:
    applicant = require_applicant(db, actor_id, lock=True)
    known = {s.id for s in stores.many(db, "get_skills_by_ids", ids=skills)}
    if known != set(skills):
        raise HTTPException(422, "Unknown skill")
    stores.execute(db, "replace_applicant_skills", applicant_id=applicant.id, skill_ids=skills)
    return get_applicant_skills(db, actor_id)
