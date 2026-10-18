"""Recruiter company/job management and admin moderation; business rules live in Python services."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, EmailStr, Field

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.api.schemas import (
    CompanyResponse,
    CompanyWrite,
    JobResponse,
    JobWrite,
    NoteRequest,
    RequestModel,
)
from app.application.companies import service as companies
from app.application.jobs import service as jobs

router = APIRouter(prefix="/api", tags=["Recruitment management"])


class MemberRequest(RequestModel):
    email: EmailStr


class MemberResponse(BaseModel):
    id: UUID
    company_id: UUID | None = None
    user_id: UUID
    membership_role: str
    full_name: str | None = None
    email: str | None = None
    created_at: datetime | None = None


class CompanyReview(RequestModel):
    decision: Literal["VERIFIED", "REJECTED"]


class SkillWrite(RequestModel):
    name: str = Field(min_length=1, max_length=100)


# Tạo công ty và OWNER membership từ user trong JWT, không nhận owner_id từ client.
@router.post("/companies", response_model=CompanyResponse, status_code=201)
def create_company(payload: CompanyWrite, db: DatabaseSession, user: CurrentUser):
    return companies.create_company(db, actor_id=user.id, data=payload.model_dump())


# Xem công ty của recruiter ngay cả khi đang PENDING.
@router.get("/recruiter/company", response_model=CompanyResponse)
def my_company(db: DatabaseSession, user: CurrentUser):
    return companies.get_my_company(db, actor_id=user.id)


# Chỉ OWNER được cập nhật hồ sơ công ty.
@router.put("/companies/{company_id}", response_model=CompanyResponse)
def update_company(company_id: UUID, payload: CompanyWrite, db: DatabaseSession, user: CurrentUser):
    return companies.update_company(
        db,
        actor_id=user.id,
        company_id=company_id,
        data=payload.model_dump(),
    )


# Recruiter xem danh sách thành viên trong công ty mình.
@router.get("/companies/{company_id}/members", response_model=list[MemberResponse])
def list_members(company_id: UUID, db: DatabaseSession, user: CurrentUser):
    return companies.list_company_members(db, actor_id=user.id, company_id=company_id)


# OWNER thêm recruiter đã có tài khoản (luồng tối thiểu, không có invitation token).
@router.post("/companies/{company_id}/members", response_model=MemberResponse, status_code=201)
def add_member(company_id: UUID, payload: MemberRequest, db: DatabaseSession, user: CurrentUser):
    return companies.add_company_member(
        db, actor_id=user.id, company_id=company_id, email=str(payload.email)
    )


# OWNER bỏ membership MEMBER, không xóa hồ sơ hoặc tài khoản người dùng.
@router.delete("/companies/{company_id}/members/{user_id}", status_code=204)
def remove_member(company_id: UUID, user_id: UUID, db: DatabaseSession, user: CurrentUser):
    companies.remove_company_member(db, actor_id=user.id, company_id=company_id, user_id=user_id)
    return Response(status_code=204)


# Admin liệt kê công ty để duyệt.
@router.get("/admin/companies", response_model=list[CompanyResponse])
def admin_companies(
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return companies.admin_list_companies(db, actor_id=user.id, limit=limit, offset=offset)


# Admin duyệt hoặc từ chối company; không có public endpoint tự cấp role ADMIN.
@router.post("/admin/companies/{company_id}/review", response_model=CompanyResponse)
def review_company(
    company_id: UUID, payload: CompanyReview, db: DatabaseSession, user: CurrentUser
):
    return companies.review_company(
        db, actor_id=user.id, company_id=company_id, decision=payload.decision
    )


# Recruiter tạo job DRAFT thuộc công ty mình.
@router.post("/companies/{company_id}/jobs", response_model=JobResponse, status_code=201)
def create_job(company_id: UUID, payload: JobWrite, db: DatabaseSession, user: CurrentUser):
    return jobs.create_job(
        db,
        actor_id=user.id,
        company_id=company_id,
        data=payload.model_dump(),
    )


# Recruiter xem cả draft/rejected jobs của công ty mình.
@router.get("/recruiter/companies/{company_id}/jobs", response_model=list[JobResponse])
def managed_jobs(
    company_id: UUID,
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return jobs.list_managed_jobs(
        db,
        actor_id=user.id,
        company_id=company_id,
        limit=limit,
        offset=offset,
    )


# Admin xem hàng đợi PENDING_APPROVAL.
@router.get("/admin/jobs/pending", response_model=list[JobResponse])
def pending_jobs(
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return jobs.list_managed_jobs(db, actor_id=user.id, company_id=None, limit=limit, offset=offset)


# Recruiter cùng công ty hoặc admin xem chi tiết và history job nội bộ.
@router.get("/recruiter/jobs/{job_id}", response_model=JobResponse)
def managed_job(job_id: UUID, db: DatabaseSession, user: CurrentUser):
    return jobs.get_managed_job(db, actor_id=user.id, job_id=job_id)


# Chỉ sửa job DRAFT hoặc REJECTED; payload không được tự gán status.
@router.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: UUID, payload: JobWrite, db: DatabaseSession, user: CurrentUser):
    return jobs.update_job(
        db,
        actor_id=user.id,
        job_id=job_id,
        data=payload.model_dump(),
    )


# State machine job: recruiter submit/close, admin approve/reject.
@router.post("/jobs/{job_id}/{action}", response_model=JobResponse)
def transition_job(
    job_id: UUID,
    action: Literal["submit", "approve", "reject", "close"],
    db: DatabaseSession,
    user: CurrentUser,
    payload: NoteRequest | None = None,
):
    return jobs.transition_job(
        db,
        actor_id=user.id,
        job_id=job_id,
        action=action,
        note=payload.note if payload else None,
    )
