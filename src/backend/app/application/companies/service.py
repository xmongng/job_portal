"""Company: Python kiểm tra quyền; các thao tác dữ liệu gọi sql/company.sql."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_company, require_role, row_dict
from app.application.common.events import audit, notify
from app.infrastructure.persistence import stores


def company_fields(data: dict) -> dict:
    values = {
        key: data.get(key) for key in ("name", "description", "industry", "location", "website_url")
    }
    if values["website_url"] is not None:
        values["website_url"] = str(values["website_url"])
    return values


# Tạo company và OWNER membership nguyên tử, không nhận owner_id từ client.
def create_company(db: Session, actor_id: UUID, data: dict) -> dict:
    require_role(db, actor_id, "RECRUITER")
    stores.one(db, "lock_user", id=actor_id)
    if stores.one(db, "get_membership_by_user", user_id=actor_id):
        raise HTTPException(409, "Recruiter already belongs to a company")
    company = stores.one(db, "insert_company", **company_fields(data))
    stores.execute(
        db,
        "insert_company_membership",
        company_id=company.id,
        user_id=actor_id,
        membership_role="OWNER",
    )
    audit(db, actor_id, "COMPANY_CREATED", company.id)
    return row_dict(company)


# Xem company của recruiter, kể cả khi đang chờ duyệt.
def get_my_company(db: Session, actor_id: UUID) -> dict:
    require_role(db, actor_id, "RECRUITER")
    member = stores.one(db, "get_membership_by_user", user_id=actor_id)
    if member is None:
        raise HTTPException(404, "Company not found")
    return row_dict(stores.one(db, "get_company_by_id", id=member.company_id))


# OWNER sửa company; company REJECTED chuyển về PENDING để admin duyệt lại.
def update_company(db: Session, actor_id: UUID, company_id: UUID, data: dict) -> dict:
    company = require_company(db, actor_id, company_id, owner_only=True)
    verification = (
        "PENDING" if company.verification_status == "REJECTED" else company.verification_status
    )
    updated = stores.one(
        db,
        "update_company_details",
        id=company_id,
        **company_fields(data),
        verification_status=verification,
    )
    audit(db, actor_id, "COMPANY_UPDATED", company_id)
    return row_dict(updated)


# Recruiter xem danh sách thành viên company mình.
def list_company_members(db: Session, actor_id: UUID, company_id: UUID) -> list[dict]:
    require_company(db, actor_id, company_id, lock=False)
    return [
        row_dict(row)
        for row in stores.many(db, "list_company_member_details", company_id=company_id)
    ]


# OWNER thêm recruiter đã có tài khoản, không tự tạo quyền từ client.
def add_company_member(db: Session, actor_id: UUID, company_id: UUID, email: str) -> dict:
    require_company(db, actor_id, company_id, owner_only=True)
    target = stores.one(db, "find_active_recruiter", email=email)
    if target is None:
        raise HTTPException(404, "Active recruiter not found")
    if stores.one(db, "get_membership_by_user", user_id=target.id):
        raise HTTPException(409, "Recruiter already belongs to a company")
    member = stores.one(
        db,
        "insert_company_membership",
        company_id=company_id,
        user_id=target.id,
        membership_role="MEMBER",
    )
    audit(db, actor_id, "MEMBER_ADDED", member.id)
    return row_dict(member)


# OWNER xóa membership MEMBER; không xóa user hoặc OWNER.
def remove_company_member(db: Session, actor_id: UUID, company_id: UUID, user_id: UUID) -> None:
    require_company(db, actor_id, company_id, owner_only=True)
    member = stores.one(db, "get_company_membership", company_id=company_id, user_id=user_id)
    if member is None or member.membership_role != "MEMBER":
        raise HTTPException(409, "Only an existing MEMBER can be removed")
    stores.execute(db, "delete_company_membership", id=member.id)
    audit(db, actor_id, "MEMBER_REMOVED", user_id)


# Admin xem danh sách company nội bộ.
def admin_list_companies(db: Session, actor_id: UUID, limit: int, offset: int) -> list[dict]:
    require_role(db, actor_id, "ADMIN")
    return [
        row_dict(c) for c in stores.many(db, "list_companies_for_admin", limit=limit, offset=offset)
    ]


# Admin quyết định duyệt; cập nhật, audit và notifications cùng transaction.
def review_company(db: Session, actor_id: UUID, company_id: UUID, decision: str) -> dict:
    require_role(db, actor_id, "ADMIN")
    company = stores.one(db, "lock_company", id=company_id)
    if company is None:
        raise HTTPException(404, "Company not found")
    if company.verification_status != "PENDING":
        raise HTTPException(409, "Company already reviewed")
    updated = stores.one(
        db, "set_company_verification", id=company_id, verification_status=decision
    )
    for member in stores.many(db, "list_memberships", company_id=company_id):
        notify(db, member.user_id, "Company reviewed", decision, "COMPANY", company_id)
    audit(db, actor_id, "COMPANY_" + decision, company_id)
    return row_dict(updated)
