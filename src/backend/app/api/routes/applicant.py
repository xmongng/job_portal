from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DatabaseSession

router = APIRouter(prefix="/api/applicants", tags=["Applicants"])


class EducationItem(BaseModel):
    school: str = Field(min_length=1, max_length=200)
    major: str = Field(min_length=1, max_length=200)
    start_year: int = Field(ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)

    @model_validator(mode="after")
    def validate_years(self) -> "EducationItem":
        if self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("end_year must be >= start_year")
        return self


class ExperienceItem(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceItem":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self


class ApplicantProfileRequest(BaseModel):
    headline: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=10000)
    location: str | None = Field(default=None, max_length=150)
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    desired_salary: Decimal | None = Field(default=None, ge=0)


class ApplicantProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    headline: str | None
    summary: str | None
    location: str | None
    education: list[EducationItem]
    experience: list[ExperienceItem]
    desired_salary: Decimal | None


# Applicant đọc hồ sơ chính chủ; chưa tạo hồ sơ trả 404.
@router.get("/me", response_model=ApplicantProfileResponse)
def get_my_profile(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> ApplicantProfileResponse:
    if current_user.role != "APPLICANT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Applicant role required",
        )

    row = (
        db.execute(
            text("SELECT * FROM public.get_applicant_profile(:user_id)"),
            {"user_id": current_user.id},
        )
        .mappings()
        .one_or_none()
    )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant profile not found",
        )

    return ApplicantProfileResponse.model_validate(row)


# Tạo hoặc thay toàn bộ hồ sơ của user trong JWT.
@router.put("/me", response_model=ApplicantProfileResponse)
def save_my_profile(
    payload: ApplicantProfileRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> ApplicantProfileResponse:
    if current_user.role != "APPLICANT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Applicant role required",
        )

    statement = text(
        """
        SELECT *
        FROM public.upsert_applicant_profile(
            :user_id,
            :headline,
            :summary,
            :location,
            :education,
            :experience,
            :desired_salary
        )
        """
    ).bindparams(
        bindparam("education", type_=JSONB),
        bindparam("experience", type_=JSONB),
    )

    try:
        row = (
            db.execute(
                statement,
                {
                    "user_id": current_user.id,
                    "headline": payload.headline,
                    "summary": payload.summary,
                    "location": payload.location,
                    "education": [item.model_dump(mode="json") for item in payload.education],
                    "experience": [item.model_dump(mode="json") for item in payload.experience],
                    "desired_salary": payload.desired_salary,
                },
            )
            .mappings()
            .one()
        )

        result = ApplicantProfileResponse.model_validate(row)
        db.commit()
        return result

    except Exception:
        db.rollback()
        raise
