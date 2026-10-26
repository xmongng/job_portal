"""Week 7: recommendation, AI drafts, admin moderation and reports."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, Field

from app.api.completion_schemas import (
    AdminUserResponse,
    CompanyStatusRequest,
    ExplanationResponse,
    JDDraft,
    JDRequest,
    JDResponse,
    MatchResponse,
    ReportResponse,
    UserStatusRequest,
)
from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.api.schemas import CompanyResponse
from app.application.admin import service as admin
from app.application.common.access import require_role
from app.application.recommendations import service as recommendations
from app.application.reports import service as reports
from app.infrastructure.ai.assistant import generate_json

router = APIRouter(prefix="/api", tags=["Recommendations, AI and admin"])


class ExplanationText(BaseModel):
    explanation: str = Field(min_length=1, max_length=10000)


# Điểm rule-based, phân trang và filters public trong store recommendation.sql.
@router.get("/recommendations", response_model=list[MatchResponse])
def recommended_jobs(
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return recommendations.recommend(db, user.id, limit, offset)


# Gửi tối thiểu facts match; không gửi email, CV, tên thật hoặc token tới provider.
@router.post("/ai/jobs/{job_id}/explain", response_model=ExplanationResponse)
def explain_match(job_id: UUID, db: DatabaseSession, user: CurrentUser):
    match = recommendations.job_match(db, user.id, job_id)
    facts = {
        key: match[key]
        for key in (
            "title",
            "score",
            "skill_score",
            "location_score",
            "salary_score",
            "matched_skills",
            "missing_skills",
        )
    }
    generated, reason = generate_json(
        "Explain this rule-based job match in Vietnamese; preserve the exact numeric score.",
        facts,
        ExplanationText,
    )
    fallback = (
        f"Điểm phù hợp theo quy tắc: {match['score']}/100. "
        f"Kỹ năng khớp: {', '.join(match['matched_skills']) or 'chưa có'}. "
        f"Kỹ năng còn thiếu: {', '.join(match['missing_skills']) or 'không có yêu cầu kỹ năng còn thiếu'}. "
        "Đây là gợi ý tham khảo, không phải quyết định tuyển dụng."
    )
    return {
        "match": match,
        "explanation": generated.explanation if generated else fallback,
        "source": "ai" if generated else "rules",
        "fallback_reason": reason,
    }


# Recruiter tạo bản nháp JD; không lưu job hoặc thay status tự động.
@router.post("/ai/job-description", response_model=JDResponse)
def generate_jd(payload: JDRequest, db: DatabaseSession, user: CurrentUser):
    require_role(db, user.id, "RECRUITER")
    generated, reason = generate_json(
        "Draft a Vietnamese job description and requirements. No invented benefits or salary.",
        payload.model_dump(),
        JDDraft,
    )
    draft = generated or JDDraft(
        description=f"Tuyển {payload.title} trong lĩnh vực {payload.category}, tại {payload.location}. Loại công việc: {payload.employment_type}.",
        requirements="Kỹ năng cần có: "
        + (", ".join(payload.skills) or "Recruiter bổ sung yêu cầu trước khi đăng."),
    )
    return {
        **draft.model_dump(),
        "source": "ai" if generated else "rules",
        "fallback_reason": reason,
        "requires_review": True,
    }


# Admin xem user DTO đã loại credentials; có filter và phân trang.
@router.get("/admin/users", response_model=list[AdminUserResponse])
def users(
    db: DatabaseSession,
    user: CurrentUser,
    keyword: str | None = Query(None, min_length=1, max_length=200),
    status: Literal["ACTIVE", "SUSPENDED"] | None = None,
    role: Literal["ADMIN", "RECRUITER", "APPLICANT"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return admin.list_users(db, user.id, keyword, status, role, limit, offset)


# Admin suspend/activate user; khi suspend thu hồi tất cả phiên.
@router.put("/admin/users/{user_id}/status", response_model=AdminUserResponse)
def user_status(user_id: UUID, payload: UserStatusRequest, db: DatabaseSession, user: CurrentUser):
    return admin.set_user_status(db, user.id, user_id, payload.status)


# Admin khóa/mở company; không thay quyết định xác minh company.
@router.put("/admin/companies/{company_id}/status", response_model=CompanyResponse)
def company_status(
    company_id: UUID, payload: CompanyStatusRequest, db: DatabaseSession, user: CurrentUser
):
    return admin.set_company_status(db, user.id, company_id, payload.status)


# Audit tối thiểu cho admin, không công khai cho recruiter/applicant.
@router.get("/admin/audit-logs")
def audit_logs(
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return admin.list_audit(db, user.id, limit, offset)


# Báo cáo JSON: admin toàn hệ thống, recruiter chỉ company mình.
@router.get("/reports/summary", response_model=ReportResponse)
def report_summary(db: DatabaseSession, user: CurrentUser, company_id: UUID | None = None):
    return reports.get_report(db, user.id, company_id)


# CSV aggregate không chứa dữ liệu cá nhân; chống rò rỉ qua kiểm tra scope trước export.
@router.get("/reports/export.csv")
def report_csv(db: DatabaseSession, user: CurrentUser, company_id: UUID | None = None):
    data = reports.get_report(db, user.id, company_id)
    return Response(
        reports.export_csv(data),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="job-portal-report.csv"',
            "Cache-Control": "no-store",
        },
    )
