"""API công khai để xem danh sách và chi tiết tin tuyển dụng."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from app.api.dependencies.database import DatabaseSession

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


# Dữ liệu ngắn gọn dùng trong trang danh sách job.
class JobSummary(BaseModel):
    id: UUID
    title: str
    company_name: str


# Dữ liệu dùng trong trang chi tiết một job.
class JobDetail(JobSummary):
    company_id: UUID
    description: str
    requirements: str | None
    location: str
    category: str
    employment_type: str
    salary_min: Decimal | None
    salary_max: Decimal | None
    deadline: datetime


# Stored function chịu trách nhiệm lọc job công khai và công ty hợp lệ.
@router.get("", response_model=list[JobSummary])
def list_jobs(db: DatabaseSession) -> list[JobSummary]:
    rows = db.execute(text("SELECT * FROM public.list_public_jobs()")).mappings().all()
    return [JobSummary.model_validate(row) for row in rows]


# Tham số :job_id được bind riêng để không nối dữ liệu người dùng vào SQL.
@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: UUID, db: DatabaseSession) -> JobDetail:
    row = (
        db.execute(
            text("SELECT * FROM public.get_public_job(:job_id)"),
            {"job_id": job_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobDetail.model_validate(row)
