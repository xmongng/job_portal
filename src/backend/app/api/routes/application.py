"""Applications, internal notes, transitions and immutable CV snapshots."""

import shutil
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.api.schemas import ApplicationResponse, ApplicationTransition, ApplyRequest, NoteRequest
from app.application.applications import service as applications
from app.application.resumes import service as resumes
from app.infrastructure.file_storage import storage_file

router = APIRouter(prefix="/api", tags=["Applications"])


# Apply bằng CV chính chủ; file snapshot không bị thay đổi khi CV gốc được cập nhật.
@router.post(
    "/applications",
    response_model=ApplicationResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def apply(payload: ApplyRequest, db: DatabaseSession, user: CurrentUser):
    resume = resumes.get_owned_resume(db, actor_id=user.id, resume_id=payload.resume_id)
    source = storage_file(resume["storage_key"])
    if not source.is_file():
        raise HTTPException(404, "Resume file unavailable")
    key = f"snapshots/{uuid4().hex}.pdf"
    target = storage_file(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(source, target)
        result = applications.apply_for_job(
            db,
            actor_id=user.id,
            job_id=payload.job_id,
            resume_id=payload.resume_id,
            letter=payload.cover_letter,
            snapshot_key=key,
        )
        result = ApplicationResponse.model_validate(result)
        db.commit()
        return result
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise


# Applicant xem đơn của chính mình; không nhận applicant_id từ client.
@router.get(
    "/applications/me", response_model=list[ApplicationResponse], response_model_exclude_unset=True
)
def my_applications(
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return applications.list_applications(
        db, actor_id=user.id, job_id=None, limit=limit, offset=offset
    )


# Recruiter xem pipeline theo job thuộc công ty mình.
@router.get(
    "/jobs/{job_id}/applications",
    response_model=list[ApplicationResponse],
    response_model_exclude_unset=True,
)
def job_applications(
    job_id: UUID,
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return applications.list_applications(
        db, actor_id=user.id, job_id=job_id, limit=limit, offset=offset
    )


# Chi tiết application đã lọc dữ liệu theo vai trò trong store.
@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    response_model_exclude_unset=True,
)
def get_application(application_id: UUID, db: DatabaseSession, user: CurrentUser):
    return applications.get_application(db, actor_id=user.id, application_id=application_id)


# Recruiter ghi chú nội bộ, applicant không nhận trường recruiter_note.
@router.put(
    "/applications/{application_id}/note",
    response_model=ApplicationResponse,
    response_model_exclude_unset=True,
)
def note(application_id: UUID, payload: NoteRequest, db: DatabaseSession, user: CurrentUser):
    return applications.set_application_note(
        db,
        actor_id=user.id,
        application_id=application_id,
        note=payload.note,
    )


# Recruiter chỉ được chuyển theo state machine; không nhảy thẳng tới HIRED.
@router.post(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse,
    response_model_exclude_unset=True,
)
def transition(
    application_id: UUID, payload: ApplicationTransition, db: DatabaseSession, user: CurrentUser
):
    return applications.transition_application(
        db,
        actor_id=user.id,
        application_id=application_id,
        next_status=payload.status,
        note=payload.note,
    )


# Applicant rút đơn trước terminal; hủy interview/offer đang chờ trong transaction.
@router.post(
    "/applications/{application_id}/withdraw",
    response_model=ApplicationResponse,
    response_model_exclude_unset=True,
)
def withdraw(application_id: UUID, db: DatabaseSession, user: CurrentUser):
    return applications.transition_application(
        db,
        actor_id=user.id,
        application_id=application_id,
        next_status="WITHDRAWN",
        note=None,
    )


# Tải snapshot CV sau kiểm tra quyền và ghi audit, không lộ storage key trong JSON.
@router.get("/applications/{application_id}/resume")
def download_application_resume(application_id: UUID, db: DatabaseSession, user: CurrentUser):
    snapshot = applications.get_application_resume(
        db, actor_id=user.id, application_id=application_id
    )
    path = storage_file(snapshot["storage_key"])
    if not path.is_file():
        raise HTTPException(404, "Resume snapshot unavailable")
    db.commit()
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=snapshot["original_name"],
        headers={"Cache-Control": "no-store"},
    )
