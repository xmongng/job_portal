"""Viết các API jobs tại đây, rồi đăng ký router trong app/main.py."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text

from app.api.dependencies.database import DatabaseSession

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

# DTO cho danh sách job: kiểm tra và trả id, tiêu đề, tên công ty.
class JobSummary(BaseModel):
    id: UUID
    title: str
    company_name: str


# DTO chi tiết job: kế thừa JobSummary, bổ sung mô tả, yêu cầu, địa điểm,
# loại việc, lương và hạn ứng tuyển; các trường có | None cho phép giá trị null.
class JobDetail(JobSummary):
    description: str
    requirements: str | None
    location_name: str
    employment_type: str
    salary_min: Decimal | None
    salary_max: Decimal | None
    deadline: datetime

# GET /api/jobs/{job_id}: gọi store get_public_job(uuid) bằng bind parameter.
# Trả chi tiết job công khai; không tìm thấy trả 404, UUID sai định dạng trả 422.
@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: UUID, db: DatabaseSession) -> JobDetail:
    row = db.execute(
        text("Select * from public.get_public_job(:job_id)"),
        {"job_id": job_id},
    ).mappings().one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return JobDetail.model_validate(row)


# GET /api/jobs: lấy danh sách job công khai có phân trang.
@router.get("", response_model=list[JobSummary])
def list_jobs(
    db: DatabaseSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[JobSummary]:
    rows = db.execute(
        text("Select * From public.list_public_jobs(:limit, :offset)"),
        {"limit": limit, "offset": offset},
    ).mappings().all()

    return [JobSummary.model_validate(row) for row in rows]
