"""Application: Python điều phối và kiểm tra nghiệp vụ; sql/application.sql đọc/ghi."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_applicant, require_company, require_role, row_dict
from app.application.common.events import audit, notify
from app.application.resumes.service import owned_resume
from app.infrastructure.persistence import stores
from app.infrastructure.persistence.stores import Record

TERMINAL_STATUSES = {"HIRED", "REJECTED", "WITHDRAWN"}
RECRUITER_TRANSITIONS = {
    "APPLIED": {"SCREENING", "REJECTED"},
    "SCREENING": {"INTERVIEW", "REJECTED"},
    "INTERVIEW": {"REJECTED"},
    "OFFER": {"REJECTED"},
}


def load_application(db: Session, application_id: UUID, *, lock: bool = False) -> Record:
    function = "lock_application" if lock else "get_application_by_id"
    application = stores.one(db, function, id=application_id)
    if application is None:
        raise HTTPException(404, "Application not found")
    return application


def application_owner(db: Session, application: Record) -> UUID:
    return stores.one(db, "get_applicant_by_id", id=application.applicant_id).user_id


def require_recruiter(db: Session, actor_id: UUID, application: Record) -> None:
    job = stores.one(db, "get_job_by_id", id=application.job_id)
    require_company(db, actor_id, job.company_id)


# Applicant chính chủ hoặc recruiter thuộc company của job.
def application_access(db: Session, actor_id: UUID, application_id: UUID) -> Record:
    application = load_application(db, application_id)
    if application_owner(db, application) == actor_id:
        require_role(db, actor_id, "APPLICANT")
    else:
        require_recruiter(db, actor_id, application)
    return application


# Chỉ gọi sau khi service kiểm tra state machine; các store dùng chung transaction.
def move_application(
    db: Session, actor_id: UUID, application: Record, next_status: str, note: str | None = None
) -> None:
    previous = application.status
    stores.execute(db, "set_application_status", id=application.id, status=next_status)
    stores.execute(
        db,
        "insert_application_history",
        application_id=application.id,
        actor_id=actor_id,
        from_status=previous,
        to_status=next_status,
        note=note,
    )
    application.status = next_status
    notify(
        db,
        application_owner(db, application),
        "Application status changed",
        next_status,
        "APPLICATION",
        application.id,
    )
    audit(db, actor_id, "APPLICATION_" + next_status, application.id)


# Chặn lộ note nội bộ và storage_key dù store trả đầy đủ record cho backend.
def get_application(db: Session, actor_id: UUID, application_id: UUID) -> dict:
    application = application_access(db, actor_id, application_id)
    own = application_owner(db, application) == actor_id
    result = row_dict(application, exclude=("resume_snapshot",))
    if own:
        result.pop("recruiter_note", None)
    snapshot = application.resume_snapshot
    result["resume_snapshot"] = (
        {k: v for k, v in snapshot.items() if k != "storage_key"} if snapshot else None
    )
    history = stores.many(db, "list_application_history", application_id=application_id)
    result["history"] = [row_dict(h, exclude=("note",) if own else ()) for h in history]
    return result


# Apply bằng CV chính chủ; history và metadata snapshot cùng transaction với đơn.
def apply_for_job(
    db: Session,
    actor_id: UUID,
    job_id: UUID,
    resume_id: UUID,
    letter: str | None,
    snapshot_key: str,
) -> dict:
    applicant = require_applicant(db, actor_id)
    job = stores.one(db, "lock_job", id=job_id)
    if job is None or job.status != "PUBLISHED" or job.deadline <= datetime.now(UTC):
        raise HTTPException(409, "Job is not open for applications")
    company = stores.one(db, "lock_company", id=job.company_id)
    if company.status != "ACTIVE" or company.verification_status != "VERIFIED":
        raise HTTPException(409, "Company is not accepting applications")
    if stores.one(db, "find_application_for_job", job_id=job_id, applicant_id=applicant.id):
        raise HTTPException(409, "Already applied to this job")
    resume = owned_resume(db, actor_id, resume_id, lock=True)
    snapshot = {
        "title": resume.title,
        "original_name": resume.original_name,
        "mime_type": resume.mime_type,
        "size_bytes": resume.size_bytes,
        "storage_key": snapshot_key,
    }
    application = stores.one(
        db,
        "insert_application",
        job_id=job_id,
        applicant_id=applicant.id,
        resume_id=resume_id,
        cover_letter=letter,
        resume_snapshot=snapshot,
    )
    stores.execute(
        db,
        "insert_application_history",
        application_id=application.id,
        actor_id=actor_id,
        from_status=None,
        to_status="APPLIED",
        note=None,
    )
    for member in stores.many(db, "list_memberships", company_id=company.id):
        notify(db, member.user_id, "New application", job.title, "APPLICATION", application.id)
    audit(db, actor_id, "APPLICATION_CREATED", application.id)
    return get_application(db, actor_id, application.id)


# Applicant xem đơn của mình; recruiter chỉ xem đơn theo job thuộc company mình.
def list_applications(
    db: Session, actor_id: UUID, job_id: UUID | None, limit: int, offset: int
) -> list[dict]:
    if job_id is None:
        applicant = require_applicant(db, actor_id)
        rows = stores.many(
            db, "list_applicant_applications", applicant_id=applicant.id, limit=limit, offset=offset
        )
    else:
        job = stores.one(db, "get_job_by_id", id=job_id)
        if job is None:
            raise HTTPException(404, "Job not found")
        require_company(db, actor_id, job.company_id, lock=False)
        rows = stores.many(db, "list_job_applications", job_id=job_id, limit=limit, offset=offset)
    return [get_application(db, actor_id, row.id) for row in rows]


# Recruiter lưu note qua store, applicant không nhận trường này trong response.
def set_application_note(
    db: Session, actor_id: UUID, application_id: UUID, note: str | None
) -> dict:
    application = load_application(db, application_id, lock=True)
    require_recruiter(db, actor_id, application)
    stores.execute(db, "set_application_note", id=application_id, recruiter_note=note)
    audit(db, actor_id, "APPLICATION_NOTE_UPDATED", application_id)
    return get_application(db, actor_id, application_id)


# Kiểm tra chuyển trạng thái trước khi gọi các store cập nhật, hủy và ghi history.
def transition_application(
    db: Session, actor_id: UUID, application_id: UUID, next_status: str, note: str | None
) -> dict:
    application = load_application(db, application_id, lock=True)
    if application.status in TERMINAL_STATUSES:
        raise HTTPException(409, "Application is terminal")
    if next_status == "WITHDRAWN":
        require_role(db, actor_id, "APPLICANT")
        if application_owner(db, application) != actor_id:
            raise HTTPException(403, "Application access denied")
    else:
        require_recruiter(db, actor_id, application)
        if next_status not in RECRUITER_TRANSITIONS.get(application.status, set()):
            raise HTTPException(409, "Invalid application transition")
    if next_status in {"REJECTED", "WITHDRAWN"}:
        stores.execute(db, "cancel_application_interviews", application_id=application_id)
        stores.execute(db, "cancel_application_offers", application_id=application_id)
    move_application(db, actor_id, application, next_status, note)
    if next_status == "WITHDRAWN":
        job = stores.one(db, "get_job_by_id", id=application.job_id)
        notify(
            db, job.created_by, "Application withdrawn", "WITHDRAWN", "APPLICATION", application_id
        )
    return get_application(db, actor_id, application_id)


# Trả file key nội bộ sau kiểm tra quyền và ghi audit qua store.
def get_application_resume(db: Session, actor_id: UUID, application_id: UUID) -> dict:
    application = application_access(db, actor_id, application_id)
    if not application.resume_snapshot or not application.resume_snapshot.get("storage_key"):
        raise HTTPException(404, "Resume snapshot unavailable")
    audit(db, actor_id, "APPLICATION_RESUME_DOWNLOADED", application_id)
    return application.resume_snapshot
