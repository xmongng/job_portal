"""Offer: Python giữ quyền/lifecycle/deadline; sql/offer.sql chỉ đọc và ghi dữ liệu."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.applications.service import (
    application_access,
    application_owner,
    load_application,
    move_application,
    require_recruiter,
)
from app.application.common.access import require_role, row_dict
from app.application.common.events import audit, notify
from app.infrastructure.persistence import stores


# Yêu cầu interview PASS, không còn lịch chờ và không có offer active khác.
def create_offer(db: Session, actor_id: UUID, application_id: UUID, data: dict) -> dict:
    application = load_application(db, application_id, lock=True)
    require_recruiter(db, actor_id, application)
    interviews = stores.many(db, "list_application_interviews", application_id=application_id)
    passed = any(i.status == "COMPLETED" and i.result == "PASS" for i in interviews)
    if application.status not in {"INTERVIEW", "OFFER"} or not passed:
        raise HTTPException(409, "Completed passing interview required")
    if any(i.status == "SCHEDULED" for i in interviews):
        raise HTTPException(409, "Complete or cancel scheduled interviews first")
    if (
        data["response_deadline"] <= datetime.now(UTC)
        or data["start_date"] < datetime.now(UTC).date()
    ):
        raise HTTPException(422, "Offer dates must be valid")
    existing = stores.many(db, "list_application_offers", application_id=application_id)
    if any(o.status in {"DRAFT", "SENT", "ACCEPTED"} for o in existing):
        raise HTTPException(409, "Application already has an active offer")
    offer = stores.one(db, "insert_offer", application_id=application_id, **data)
    audit(db, actor_id, "OFFER_DRAFTED", offer.id)
    return row_dict(offer)


# Kiểm tra quyền, ẩn DRAFT khỏi applicant và tính is_expired theo thời gian thực.
def get_offer(db: Session, actor_id: UUID, offer_id: UUID) -> dict:
    offer = stores.one(db, "get_offer_by_id", id=offer_id)
    if offer is None:
        raise HTTPException(404, "Offer not found")
    application = application_access(db, actor_id, offer.application_id)
    if offer.status == "DRAFT" and application_owner(db, application) == actor_id:
        raise HTTPException(404, "Offer not found")
    expired = offer.status == "EXPIRED" or (
        offer.status == "SENT" and offer.response_deadline <= datetime.now(UTC)
    )
    return {**row_dict(offer), "is_expired": expired}


# Send/accept/reject/expire; các store cập nhật cùng transaction với application/history.
def transition_offer(db: Session, actor_id: UUID, offer_id: UUID, action: str) -> dict:
    offer = stores.one(db, "get_offer_by_id", id=offer_id)
    if offer is None:
        raise HTTPException(404, "Offer not found")
    application = load_application(db, offer.application_id, lock=True)
    offer = stores.one(db, "get_offer_by_id", id=offer_id)
    owner_id = application_owner(db, application)
    now = datetime.now(UTC)
    if action == "send":
        require_recruiter(db, actor_id, application)
        if (
            offer.status != "DRAFT"
            or application.status not in {"INTERVIEW", "OFFER"}
            or offer.response_deadline <= now
            or offer.start_date < now.date()
        ):
            raise HTTPException(409, "Offer cannot be sent")
        next_status = "SENT"
        if application.status != "OFFER":
            move_application(db, actor_id, application, "OFFER")
    elif action in {"accept", "reject"}:
        require_role(db, actor_id, "APPLICANT")
        if owner_id != actor_id:
            raise HTTPException(403, "Offer access denied")
        if (
            offer.status != "SENT"
            or application.status != "OFFER"
            or offer.response_deadline <= now
        ):
            raise HTTPException(409, "Offer is not pending or has expired")
        next_status = "ACCEPTED" if action == "accept" else "REJECTED"
        move_application(db, actor_id, application, "HIRED" if action == "accept" else "REJECTED")
    elif action == "expire":
        if actor_id == owner_id:
            require_role(db, actor_id, "APPLICANT")
        else:
            require_recruiter(db, actor_id, application)
        if offer.status != "SENT" or offer.response_deadline > now:
            raise HTTPException(409, "Offer has not expired")
        next_status = "EXPIRED"
    else:
        raise HTTPException(422, "Invalid offer action")
    stores.execute(db, "set_offer_status", id=offer_id, status=next_status)
    notify(db, owner_id, "Offer updated", action, "OFFER", offer_id)
    job = stores.one(db, "get_job_by_id", id=application.job_id)
    notify(db, job.created_by, "Offer updated", action, "OFFER", offer_id)
    audit(db, actor_id, "OFFER_" + action.upper(), offer_id)
    return get_offer(db, actor_id, offer_id)


# Đọc các offer bằng store rồi lọc draft theo người gọi.
def list_offers(db: Session, actor_id: UUID, application_id: UUID) -> list[dict]:
    application = application_access(db, actor_id, application_id)
    own = application_owner(db, application) == actor_id
    rows = stores.many(db, "list_application_offers", application_id=application_id)
    return [get_offer(db, actor_id, o.id) for o in rows if not own or o.status != "DRAFT"]
