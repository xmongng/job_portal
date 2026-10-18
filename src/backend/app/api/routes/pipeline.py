"""Interview, offer and in-app notification APIs through Week 6."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.api.schemas import (
    InterviewResponse,
    InterviewResult,
    InterviewWrite,
    NotificationResponse,
    OfferResponse,
    OfferWrite,
)
from app.application.interviews import service as interviews_service
from app.application.notifications import service as notifications_service
from app.application.offers import service as offers

router = APIRouter(prefix="/api", tags=["Interviews and offers"])


# Recruiter đặt lịch cho application INTERVIEW; từ chối lịch trùng hoặc vòng trùng.
@router.post(
    "/applications/{application_id}/interviews",
    response_model=InterviewResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def schedule(application_id: UUID, payload: InterviewWrite, db: DatabaseSession, user: CurrentUser):
    return interviews_service.schedule_interview(
        db,
        actor_id=user.id,
        application_id=application_id,
        data=payload.model_dump(),
    )


# Applicant/recruiter xem lịch theo application; feedback nội bộ chỉ cho recruiter.
@router.get(
    "/applications/{application_id}/interviews",
    response_model=list[InterviewResponse],
    response_model_exclude_unset=True,
)
def interviews(application_id: UUID, db: DatabaseSession, user: CurrentUser):
    return interviews_service.list_interviews(db, actor_id=user.id, application_id=application_id)


# Recruiter hủy interview còn SCHEDULED.
@router.post("/interviews/{interview_id}/cancel", response_model=InterviewResponse)
def cancel_interview(interview_id: UUID, db: DatabaseSession, user: CurrentUser):
    return interviews_service.update_interview(
        db,
        actor_id=user.id,
        interview_id=interview_id,
        action="cancel",
        result=None,
        feedback=None,
    )


# Recruiter ghi kết quả sau khi interview đã bắt đầu.
@router.post("/interviews/{interview_id}/result", response_model=InterviewResponse)
def interview_result(
    interview_id: UUID, payload: InterviewResult, db: DatabaseSession, user: CurrentUser
):
    return interviews_service.update_interview(
        db,
        actor_id=user.id,
        interview_id=interview_id,
        action="result",
        result=payload.result,
        feedback=payload.feedback,
    )


# Recruiter tạo draft offer sau interview PASS.
@router.post("/applications/{application_id}/offers", response_model=OfferResponse, status_code=201)
def create_offer(application_id: UUID, payload: OfferWrite, db: DatabaseSession, user: CurrentUser):
    return offers.create_offer(
        db,
        actor_id=user.id,
        application_id=application_id,
        data=payload.model_dump(),
    )


# Applicant không thấy draft offers; recruiter phải thuộc công ty của application.
@router.get("/applications/{application_id}/offers", response_model=list[OfferResponse])
def list_offers(application_id: UUID, db: DatabaseSession, user: CurrentUser):
    return offers.list_offers(db, actor_id=user.id, application_id=application_id)


# Chi tiết offer cùng cờ is_expired, kể cả khi chưa chạy thao tác expire.
@router.get("/offers/{offer_id}", response_model=OfferResponse)
def get_offer(offer_id: UUID, db: DatabaseSession, user: CurrentUser):
    return offers.get_offer(db, actor_id=user.id, offer_id=offer_id)


# Recruiter send; applicant accept/reject; expire chỉ sau response_deadline.
@router.post("/offers/{offer_id}/{action}", response_model=OfferResponse)
def offer_action(
    offer_id: UUID,
    action: Literal["send", "accept", "reject", "expire"],
    db: DatabaseSession,
    user: CurrentUser,
):
    return offers.transition_offer(db, actor_id=user.id, offer_id=offer_id, action=action)


# User xem thông báo của chính mình, không nhận user_id từ client.
@router.get("/notifications", response_model=list[NotificationResponse])
def notifications(
    db: DatabaseSession,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return notifications_service.list_notifications(
        db, actor_id=user.id, limit=limit, offset=offset
    )


# User đánh dấu thông báo chính chủ đã đọc.
@router.put("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: UUID, db: DatabaseSession, user: CurrentUser):
    return notifications_service.read_notification(
        db, actor_id=user.id, notification_id=notification_id
    )
