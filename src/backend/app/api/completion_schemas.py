"""DTO cho recommendation, AI và quản trị; không nhận dữ liệu tài khoản nhạy cảm."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas import RequestModel


class MatchResponse(BaseModel):
    id: UUID
    title: str
    company_name: str
    location: str
    salary_min: Decimal | None
    salary_max: Decimal | None
    skill_score: int
    location_score: int
    salary_score: int
    score: int
    matched_skills: list[str]
    missing_skills: list[str]


class ExplanationResponse(BaseModel):
    match: MatchResponse
    explanation: str
    source: Literal["rules", "ai"]
    fallback_reason: str | None = None


class JDRequest(RequestModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=120)
    skills: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        default_factory=list, max_length=50
    )
    location: str = Field(min_length=1, max_length=150)
    employment_type: Literal["FULL_TIME", "PART_TIME", "INTERNSHIP", "CONTRACT"] = "FULL_TIME"


class JDDraft(BaseModel):
    description: str = Field(min_length=1, max_length=20000)
    requirements: str = Field(min_length=1, max_length=10000)


class JDResponse(JDDraft):
    source: Literal["rules", "ai"]
    fallback_reason: str | None = None
    requires_review: bool = True


class UserStatusRequest(RequestModel):
    status: Literal["ACTIVE", "SUSPENDED"]


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime


class CompanyStatusRequest(RequestModel):
    status: Literal["ACTIVE", "SUSPENDED"]


class StatusCount(BaseModel):
    status: str
    total: int


class Counts(BaseModel):
    companies: int
    jobs: int
    applications: int
    interviews: int
    offers: int


class ReportResponse(BaseModel):
    company_id: UUID | None
    counts: Counts
    jobs: list[StatusCount]
    applications: list[StatusCount]
