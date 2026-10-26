"""Admin moderation; mọi đọc/ghi dữ liệu qua sql/admin.sql và store hiện có."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_role, row_dict
from app.application.common.events import audit, notify
from app.infrastructure.persistence import stores


# Liệt kê DTO tài khoản, không lấy password/token từ store này.
def list_users(
    db: Session,
    actor_id: UUID,
    keyword: str | None,
    status: str | None,
    role: str | None,
    limit: int,
    offset: int,
):
    require_role(db, actor_id, "ADMIN")
    return [
        row_dict(u)
        for u in stores.many(
            db,
            "list_admin_users",
            keyword=keyword,
            status=status,
            role=role,
            limit=limit,
            offset=offset,
        )
    ]


# Suspend user thu hồi mọi session; không tự khóa hoặc khóa admin cuối cùng.
def set_user_status(db: Session, actor_id: UUID, user_id: UUID, status: str):
    require_role(db, actor_id, "ADMIN")
    stores.execute(db, "lock_admin_moderation")
    # Recheck after serialization: another admin may have suspended the actor while waiting.
    require_role(db, actor_id, "ADMIN")
    target = stores.one(db, "lock_user", id=user_id)
    if target is None:
        raise HTTPException(404, "User not found")
    if status == "SUSPENDED":
        if target.id == actor_id:
            raise HTTPException(409, "Cannot suspend your own account")
        if (
            target.role == "ADMIN"
            and target.status == "ACTIVE"
            and stores.one(db, "count_active_admins").total <= 1
        ):
            raise HTTPException(409, "Cannot suspend the last active admin")
        stores.execute(db, "revoke_user_sessions", user_id=user_id)
    result = stores.one(db, "set_user_status", id=user_id, status=status)
    audit(db, actor_id, "USER_" + status, user_id)
    return row_dict(result)


# Admin suspend company khiến public jobs ẩn và recruiter không được sửa tài nguyên.
def set_company_status(db: Session, actor_id: UUID, company_id: UUID, status: str):
    require_role(db, actor_id, "ADMIN")
    company = stores.one(db, "lock_company", id=company_id)
    if company is None:
        raise HTTPException(404, "Company not found")
    result = stores.one(db, "set_company_status", id=company_id, status=status)
    for member in stores.many(db, "list_memberships", company_id=company_id):
        notify(db, member.user_id, "Company status changed", status, "COMPANY", company_id)
    audit(db, actor_id, "COMPANY_" + status, company_id)
    return row_dict(result)


# Audit chỉ dành cho admin; không có password/CV content trong dữ liệu này.
def list_audit(db: Session, actor_id: UUID, limit: int, offset: int):
    require_role(db, actor_id, "ADMIN")
    return [
        row_dict(row) for row in stores.many(db, "list_admin_audit", limit=limit, offset=offset)
    ]
