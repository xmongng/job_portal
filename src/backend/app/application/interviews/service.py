"""Interview: Python kiểm tra lịch; mọi truy vấn và ghi kết quả qua sql/interview.sql."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.applications.service import (
    application_access,
    application_owner,
    load_application,
    require_recruiter,
)
from app.application.common.access import row_dict
from app.application.common.events import audit, notify
from app.infrastructure.persistence import stores


# Khóa scheduling, kiểm tra company/applicant và khoảng thời gian trước khi ghi lịch.
def schedule_interview(db: Session, actor_id: UUID, application_id: UUID, data: dict) -> dict:
    stores.execute(db, "lock_interview_schedule")
    application = load_application(db, application_id, lock=True)
    require_recruiter(db, actor_id, application)
    if application.status != "INTERVIEW":
        raise HTTPException(409, "Application must be in INTERVIEW")
    start = data["scheduled_at"]
    end = start + timedelta(minutes=data["duration_minutes"])
    if start <= datetime.now(UTC):
        raise HTTPException(422, "Interview must be in the future")
    job = stores.one(db, "get_job_by_id", id=application.job_id)
    scheduled = stores.many(
        db,
        "list_conflicting_interview_candidates",
        company_id=job.company_id,
        applicant_id=application.applicant_id,
        end_at=end,
    )
    for previous in scheduled:
        if start < previous.scheduled_at + timedelta(minutes=previous.duration_minutes):
            raise HTTPException(409, "Interview overlaps applicant or company schedule")
    interview = stores.one(db, "insert_interview", application_id=application_id, **data)
    notify(
        db,
        application_owner(db, application),
        "Interview scheduled",
        start.isoformat(),
        "INTERVIEW",
        interview.id,
    )
    audit(db, actor_id, "INTERVIEW_SCHEDULED", interview.id)
    return row_dict(interview, exclude=("feedback",))


# Khóa application trước khi hủy hoặc ghi kết quả, tránh race với withdraw.
def update_interview(
    db: Session,
    actor_id: UUID,
    interview_id: UUID,
    action: str,
    result: str | None,
    feedback: str | None,
) -> dict:
    interview = stores.one(db, "get_interview_by_id", id=interview_id)
    if interview is None:
        raise HTTPException(404, "Interview not found")
    application = load_application(db, interview.application_id, lock=True)
    interview = stores.one(db, "get_interview_by_id", id=interview_id)
    require_recruiter(db, actor_id, application)
    if interview.status != "SCHEDULED" or application.status != "INTERVIEW":
        raise HTTPException(409, "Interview is not editable")
    if action == "cancel":
        status = "CANCELLED"
        result = interview.result
        feedback = interview.feedback
    else:
        if interview.scheduled_at > datetime.now(UTC):
            raise HTTPException(409, "Interview has not started")
        status = "COMPLETED"
    updated = stores.one(
        db, "set_interview_result", id=interview_id, status=status, result=result, feedback=feedback
    )
    notify(
        db,
        application_owner(db, application),
        "Interview updated",
        status,
        "INTERVIEW",
        interview_id,
    )
    audit(db, actor_id, "INTERVIEW_" + status, interview_id)
    return row_dict(updated)


# Đọc lịch qua store và bỏ feedback nội bộ khỏi response applicant.
def list_interviews(db: Session, actor_id: UUID, application_id: UUID) -> list[dict]:
    application = application_access(db, actor_id, application_id)
    own = application_owner(db, application) == actor_id
    return [
        row_dict(i, exclude=("feedback",) if own else ())
        for i in stores.many(db, "list_application_interviews", application_id=application_id)
    ]
