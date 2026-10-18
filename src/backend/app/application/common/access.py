"""Quyền trong Python; dữ liệu để kiểm tra luôn lấy qua store trong sql/."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.persistence import stores
from app.infrastructure.persistence.stores import Record


def row_dict(row: Record, *, exclude: tuple[str, ...] = ()) -> dict:
    return {key: value for key, value in vars(row).items() if key not in exclude}


# Lấy user bằng store, sau đó kiểm tra trạng thái và role ở Python.
def require_role(db: Session, actor_id: UUID, role: str) -> Record:
    user = stores.one(db, "get_user_by_id", id=actor_id)
    if user is None or user.status != "ACTIVE" or user.role != role:
        raise HTTPException(403, f"{role} role required")
    return user


# Kiểm tra recruiter thuộc company; owner_only dùng khi sửa company/thành viên.
def require_company(
    db: Session, actor_id: UUID, company_id: UUID, *, owner_only: bool = False, lock: bool = True
) -> Record:
    require_role(db, actor_id, "RECRUITER")
    function = "lock_company" if lock else "get_company_by_id"
    company = stores.one(db, function, id=company_id)
    membership = stores.one(db, "get_company_membership", company_id=company_id, user_id=actor_id)
    if company is None or company.status != "ACTIVE" or membership is None:
        raise HTTPException(403, "Company access denied")
    if owner_only and membership.membership_role != "OWNER":
        raise HTTPException(403, "Company OWNER required")
    return company


# Xác định applicant chính chủ; dùng store khóa row khi thay skills/default CV.
def require_applicant(db: Session, actor_id: UUID, *, lock: bool = False) -> Record:
    require_role(db, actor_id, "APPLICANT")
    function = "lock_applicant_by_user" if lock else "get_applicant_by_user"
    applicant = stores.one(db, function, user_id=actor_id)
    if applicant is None:
        raise HTTPException(404, "Create applicant profile first")
    return applicant
