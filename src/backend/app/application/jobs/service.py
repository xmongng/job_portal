"""Job lifecycle trong Python; mọi đọc/ghi thực hiện bằng store trong sql/job.sql."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_company, require_role, row_dict
from app.application.common.events import audit, notify
from app.infrastructure.persistence import stores
from app.infrastructure.persistence.stores import Record


def load_job(db: Session, job_id: UUID, *, lock: bool = True) -> Record:
    job = stores.one(db, "lock_job" if lock else "get_job_by_id", id=job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job


def job_fields(db: Session, data: dict) -> dict:
    if data["deadline"] <= datetime.now(UTC):
        raise HTTPException(422, "Deadline must be in the future")
    known = {s.id for s in stores.many(db, "get_skills_by_ids", ids=data["skill_ids"])}
    if known != set(data["skill_ids"]):
        raise HTTPException(422, "Unknown skill")
    return {
        key: data.get(key)
        for key in (
            "title",
            "description",
            "requirements",
            "location",
            "category",
            "employment_type",
            "salary_min",
            "salary_max",
            "deadline",
        )
    }


# Tạo draft, skills và lịch sử trong cùng transaction.
def create_job(db: Session, actor_id: UUID, company_id: UUID, data: dict) -> dict:
    require_company(db, actor_id, company_id)
    job = stores.one(
        db, "insert_job", company_id=company_id, created_by=actor_id, **job_fields(db, data)
    )
    stores.execute(db, "replace_job_skills", job_id=job.id, skill_ids=data["skill_ids"])
    stores.execute(
        db,
        "insert_job_history",
        job_id=job.id,
        actor_id=actor_id,
        from_status=None,
        to_status="DRAFT",
        note=None,
    )
    audit(db, actor_id, "JOB_CREATED", job.id)
    return row_dict(job)


# Chỉ sửa job chưa submit hoặc đã bị admin từ chối.
def update_job(db: Session, actor_id: UUID, job_id: UUID, data: dict) -> dict:
    job = load_job(db, job_id)
    require_company(db, actor_id, job.company_id)
    if job.status not in {"DRAFT", "REJECTED"}:
        raise HTTPException(409, "Only draft or rejected jobs can be edited")
    updated = stores.one(db, "update_job_details", id=job_id, **job_fields(db, data))
    stores.execute(db, "replace_job_skills", job_id=job_id, skill_ids=data["skill_ids"])
    audit(db, actor_id, "JOB_UPDATED", job_id)
    return row_dict(updated)


# Recruiter submit/close, admin approve/reject; Python kiểm tra state trước khi gọi store.
def transition_job(
    db: Session, actor_id: UUID, job_id: UUID, action: str, note: str | None
) -> dict:
    job = load_job(db, job_id)
    previous = job.status
    if action in {"approve", "reject"}:
        require_role(db, actor_id, "ADMIN")
        if previous != "PENDING_APPROVAL":
            raise HTTPException(409, "Job is not pending approval")
        if action == "reject":
            if not note or not note.strip():
                raise HTTPException(422, "Rejection reason required")
            next_status = "REJECTED"
        else:
            company = stores.one(db, "get_company_by_id", id=job.company_id)
            if (
                company.status != "ACTIVE"
                or company.verification_status != "VERIFIED"
                or job.deadline <= datetime.now(UTC)
            ):
                raise HTTPException(409, "Verified active company and future deadline required")
            next_status = "PUBLISHED"
    else:
        company = require_company(db, actor_id, job.company_id)
        if action == "submit" and previous in {"DRAFT", "REJECTED"}:
            if company.verification_status != "VERIFIED" or job.deadline <= datetime.now(UTC):
                raise HTTPException(409, "Verified company and future deadline required")
            next_status = "PENDING_APPROVAL"
        elif action == "close" and previous == "PUBLISHED":
            next_status = "CLOSED"
        else:
            raise HTTPException(409, "Invalid job transition")
    updated = stores.one(db, "set_job_status", id=job_id, status=next_status)
    stores.execute(
        db,
        "insert_job_history",
        job_id=job_id,
        actor_id=actor_id,
        from_status=previous,
        to_status=next_status,
        note=note,
    )
    notify(db, job.created_by, "Job status changed", next_status, "JOB", job_id)
    audit(db, actor_id, "JOB_" + next_status, job_id)
    return row_dict(updated)


# Chọn đúng store danh sách company hoặc hàng đợi admin sau khi kiểm tra quyền.
def list_managed_jobs(
    db: Session, actor_id: UUID, company_id: UUID | None, limit: int, offset: int
) -> list[dict]:
    if company_id is None:
        require_role(db, actor_id, "ADMIN")
        rows = stores.many(db, "list_pending_jobs", limit=limit, offset=offset)
    else:
        require_company(db, actor_id, company_id, lock=False)
        rows = stores.many(
            db, "list_company_managed_jobs", company_id=company_id, limit=limit, offset=offset
        )
    return [row_dict(job) for job in rows]


# Chi tiết nội bộ gồm skills và history; API public chỉ trả thông tin công khai.
def get_managed_job(db: Session, actor_id: UUID, job_id: UUID) -> dict:
    job = load_job(db, job_id, lock=False)
    user = stores.one(db, "get_user_by_id", id=actor_id)
    if user.role != "ADMIN":
        require_company(db, actor_id, job.company_id, lock=False)
    else:
        require_role(db, actor_id, "ADMIN")
    return {
        **row_dict(job),
        "skills": [row_dict(s) for s in stores.many(db, "get_job_skills", job_id=job_id)],
        "history": [row_dict(h) for h in stores.many(db, "list_job_history", job_id=job_id)],
    }
