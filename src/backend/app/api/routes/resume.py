"""Private CV upload/default/delete/download APIs."""

import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.api.schemas import ResumeResponse
from app.application.resumes import service as resumes
from app.infrastructure.file_storage import save_pdf, storage_file

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])
logger = logging.getLogger(__name__)


# Upload PDF private; dọn file nếu transaction lưu metadata thất bại.
@router.post("", response_model=ResumeResponse, status_code=201)
def upload_resume(
    db: DatabaseSession,
    user: CurrentUser,
    title: Annotated[str, Form(min_length=1, max_length=150)],
    file: Annotated[UploadFile, File()],
):
    resumes.check_applicant(db, actor_id=user.id)
    if not title.strip():
        raise HTTPException(422, "Title must not be blank")
    key, size = save_pdf(file)
    try:
        result = resumes.create_resume(
            db,
            actor_id=user.id,
            data={
                "title": title.strip(),
                "storage_key": key,
                "original_name": Path(file.filename or "resume.pdf").name[:255],
                "size_bytes": size,
            },
        )
        result = ResumeResponse.model_validate(result)
        db.commit()
        return result
    except Exception:
        db.rollback()
        storage_file(key).unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


# Chỉ liệt kê metadata của CV chính chủ, không trả storage_key.
@router.get("", response_model=list[ResumeResponse])
def list_resumes(
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return resumes.list_resumes(db, actor_id=user.id, limit=limit, offset=offset)


# Đặt CV mặc định; database bảo đảm tối đa một default/applicant.
@router.put("/{resume_id}/default", response_model=ResumeResponse)
def default_resume(resume_id: UUID, db: DatabaseSession, user: CurrentUser):
    return resumes.set_default_resume(db, actor_id=user.id, resume_id=resume_id)


# Tải CV chính chủ qua endpoint có xác thực, không public mount thư mục file.
@router.get("/{resume_id}/download")
def download_resume(resume_id: UUID, db: DatabaseSession, user: CurrentUser):
    resume = resumes.get_owned_resume(db, actor_id=user.id, resume_id=resume_id)
    path = storage_file(resume["storage_key"])
    if not path.is_file():
        raise HTTPException(404, "Resume file unavailable")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=resume["original_name"],
        headers={"Cache-Control": "no-store"},
    )


# Rename tạm trước commit; rollback khôi phục file. CV đã được dùng trả 409.
@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: UUID, db: DatabaseSession, user: CurrentUser):
    resume = resumes.delete_resume(db, actor_id=user.id, resume_id=resume_id)
    path = storage_file(resume["storage_key"])
    tombstone = path.with_name(f"{uuid4().hex}.deleted")
    moved = False
    try:
        if path.is_file():
            path.rename(tombstone)
            moved = True
        db.commit()
    except Exception:
        db.rollback()
        if moved:
            tombstone.rename(path)
        raise
    if moved:
        try:
            tombstone.unlink(missing_ok=True)
        except OSError:
            logger.warning("Private tombstone cleanup deferred")
    return Response(status_code=204)
