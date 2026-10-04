"""Viết các API company tại đây, rồi đăng ký router trong app/main.py."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from app.api.dependencies.database import DatabaseSession

router = APIRouter(prefix='/api/companies', tags=['Companies'])

class CompanySummary(BaseModel):
    id: UUID
    name: str
    industry: str
    location_name: str

class CompanyDetail(CompanySummary):
    description: str | None
    website_url: str | None
    

class CompanyJobSummary(BaseModel):
    id: UUID
    title: str
    company_name: str


# GET /api/companies: gọi store list_public_companies() và trả danh sách công ty công khai.
@router.get('', response_model=list[CompanySummary])
def list_companies(db: DatabaseSession)-> list[CompanySummary]:
    rows = db.execute(
        text('select *from public.list_public_companies()')).mappings().all()
    return [CompanySummary.model_validate(row) for row in rows]


# GET /api/companies/{company_id}: gọi store get_public_company(uuid) để lấy chi tiết.
# Trả 404 nếu không có công ty công khai phù hợp; UUID sai định dạng được FastAPI trả 422.
@router.get("/{company_id}", response_model=CompanyDetail)
def get_company(company_id: UUID, db: DatabaseSession) -> CompanyDetail:
    row = db.execute(
        text("SELECT * FROM public.get_public_company(:company_id)"),
        {"company_id": company_id},
    ).mappings().one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return CompanyDetail.model_validate(row)



# GET /api/companies/{company_id}/jobs: lấy các job công khai của công ty.
# Công ty không công khai hoặc không tồn tại trả 404; chưa có job trả [].
@router.get("/{company_id}/jobs", response_model=list[CompanyJobSummary])
def list_company_job(company_id: UUID, db: DatabaseSession) -> list[CompanyJobSummary]:
    company = db.execute(
        text("SELECT * FROM public.get_public_company(:company_id)"),
        {"company_id": company_id},
    ).mappings().one_or_none()

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    rows = db.execute(
        text("SELECT * FROM public.list_public_company_jobs(:company_id)"),
        {"company_id": company_id},
    ).mappings().all()

    return [CompanyJobSummary.model_validate(row) for row in rows]

