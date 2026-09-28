"""Các API công khai để xem công ty và tin tuyển dụng của công ty."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.dependencies.database import DatabaseSession
from app.infrastructure.persistence.models.companies import Company
from app.infrastructure.persistence.models.jobs import Job

router = APIRouter(prefix="/api/companies", tags=["Companies"])


# Chỉ công bố những thông tin cơ bản, không trả về dữ liệu duyệt nội bộ.
class CompanySummary(BaseModel):
    id: UUID
    name: str
    industry: str
    location_name: str


# Dữ liệu tóm tắt của một tin thuộc công ty được chọn.
class CompanyJobSummary(BaseModel):
    id: UUID
    title: str
    company_name: str


# GET /api/companies: danh sách công ty đã xác minh và đang hoạt động.
@router.get("", response_model=list[CompanySummary])
def list_companies(db: DatabaseSession) -> list[CompanySummary]:
    statement = (
        select(Company.id, Company.name, Company.industry, Company.location.label("location_name"))
        .where(Company.verification_status == "VERIFIED", Company.status == "ACTIVE")
        .order_by(Company.name, Company.id)
        .limit(20)
    )
    return [CompanySummary.model_validate(row._mapping) for row in db.execute(statement)]


# GET /api/companies/{company_id}/jobs: các tin công khai của một công ty.
@router.get("/{company_id}/jobs", response_model=list[CompanyJobSummary])
def list_company_jobs(company_id: UUID, db: DatabaseSession) -> list[CompanyJobSummary]:
    # Trả 404 nếu công ty không tồn tại hoặc không được hiển thị công khai.
    company_id_found = db.scalar(
        select(Company.id).where(
            Company.id == company_id,
            Company.verification_status == "VERIFIED",
            Company.status == "ACTIVE",
        )
    )
    if company_id_found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Công ty tồn tại nhưng chưa có tin phù hợp sẽ trả danh sách rỗng.
    statement = (
        select(Job.id, Job.title, Company.name.label("company_name"))
        .join(Company, Job.company_id == Company.id)
        .where(
            Job.company_id == company_id,
            Job.status == "PUBLISHED",
            Job.deadline > datetime.now(UTC),
        )
        .order_by(Job.created_at.desc(), Job.id)
        .limit(20)
    )
    return [CompanyJobSummary.model_validate(row._mapping) for row in db.execute(statement)]
