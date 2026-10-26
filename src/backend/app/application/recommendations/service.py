"""Score chỉ tính trong store bằng quy tắc; AI không được thay đổi score/trạng thái."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_applicant, row_dict
from app.infrastructure.persistence import stores


# Job recommendations cho applicant đã có profile; public filters luôn được áp dụng.
def recommend(db: Session, user_id: UUID, limit: int, offset: int):
    require_applicant(db, user_id)
    return [
        row_dict(r)
        for r in stores.many(db, "recommend_jobs", user_id=user_id, limit=limit, offset=offset)
    ]


# Lấy facts match của một job hợp lệ, dùng làm đầu vào tối thiểu cho AI explanation.
def job_match(db: Session, user_id: UUID, job_id: UUID):
    require_applicant(db, user_id)
    result = stores.one(db, "get_job_match", user_id=user_id, job_id=job_id)
    if result is None:
        raise HTTPException(404, "Public job not found")
    return row_dict(result)
