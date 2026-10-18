"""Allowlisted request/response DTOs for recruitment workflows."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CompanyWrite(RequestModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    industry: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=150)
    website_url: HttpUrl | None = None


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    industry: str
    location: str
    website_url: str | None
    verification_status: str
    status: str
    created_at: datetime
    updated_at: datetime


class JobWrite(RequestModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=30000)
    requirements: str | None = Field(default=None, max_length=30000)
    location: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=120)
    employment_type: Literal["FULL_TIME", "PART_TIME", "INTERNSHIP", "CONTRACT"]
    salary_min: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    salary_max: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    deadline: AwareDatetime
    skill_ids: list[UUID] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_salary_and_skills(self) -> "JobWrite":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("salary_max must be >= salary_min")
        if len(self.skill_ids) != len(set(self.skill_ids)):
            raise ValueError("Duplicate skill IDs")
        return self


class JobResponse(BaseModel):
    id: UUID
    company_id: UUID
    created_by: UUID
    title: str
    description: str
    requirements: str | None
    location: str
    category: str
    employment_type: str
    salary_min: Decimal | None
    salary_max: Decimal | None
    deadline: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    skills: list[dict[str, Any]] | None = None
    history: list[dict[str, Any]] | None = None


class SkillResponse(BaseModel):
    id: UUID
    name: str


class SkillsWrite(RequestModel):
    skill_ids: list[UUID] = Field(max_length=100)

    @model_validator(mode="after")
    def unique_ids(self) -> "SkillsWrite":
        if len(self.skill_ids) != len(set(self.skill_ids)):
            raise ValueError("Duplicate skill IDs")
        return self


class ResumeResponse(BaseModel):
    id: UUID
    applicant_id: UUID
    title: str
    original_name: str
    mime_type: str
    size_bytes: int
    is_default: bool
    created_at: datetime


class ApplyRequest(RequestModel):
    job_id: UUID
    resume_id: UUID
    cover_letter: str | None = Field(default=None, max_length=10000)


class ApplicationResponse(BaseModel):
    id: UUID
    job_id: UUID
    applicant_id: UUID
    resume_id: UUID
    cover_letter: str | None
    status: str
    recruiter_note: str | None = None
    resume_snapshot: dict[str, Any] | None
    history: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class NoteRequest(RequestModel):
    note: str | None = Field(default=None, max_length=10000)


class ApplicationTransition(NoteRequest):
    status: Literal["SCREENING", "INTERVIEW", "REJECTED"]


class InterviewWrite(RequestModel):
    round_number: int = Field(ge=1, le=100)
    scheduled_at: AwareDatetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    mode: Literal["ONLINE", "OFFLINE"]
    location_or_url: str = Field(min_length=1, max_length=500)


class InterviewResult(RequestModel):
    result: Literal["PASS", "FAIL"]
    feedback: str | None = Field(default=None, max_length=10000)


class InterviewResponse(BaseModel):
    id: UUID
    application_id: UUID
    round_number: int
    scheduled_at: datetime
    duration_minutes: int
    mode: str
    location_or_url: str
    status: str
    result: str | None
    feedback: str | None = None
    created_at: datetime


class OfferWrite(RequestModel):
    salary: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    start_date: date
    response_deadline: AwareDatetime
    terms: str | None = Field(default=None, max_length=20000)


class OfferResponse(BaseModel):
    id: UUID
    application_id: UUID
    salary: Decimal
    start_date: date
    response_deadline: datetime
    terms: str | None
    status: str
    is_expired: bool = False
    created_at: datetime
    updated_at: datetime


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    body: str
    resource_type: str | None
    resource_id: UUID | None
    read_at: datetime | None
    created_at: datetime
