"""Refresh/logout: Python kiểm tra điều kiện, SQL store thực hiện đọc/ghi."""

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_refresh_token
from app.infrastructure.persistence import stores
from app.infrastructure.persistence.stores import Record


# Khóa phiên theo hash, kiểm tra hiệu lực, rồi cập nhật hash trong cùng transaction.
def rotate_session(db: Session, old_token: str, new_token: str) -> Record:
    session = stores.one(db, "lock_auth_session_by_hash", hash=hash_refresh_token(old_token))
    if session is None or session.revoked_at is not None or session.expires_at <= datetime.now(UTC):
        raise HTTPException(401, "Invalid or expired refresh token")
    user = stores.one(db, "get_user_by_id", id=session.user_id)
    if user is None or user.status != "ACTIVE":
        raise HTTPException(401, "Account is unavailable")
    return stores.one(
        db, "set_auth_session_hash", id=session.id, refresh_token_hash=hash_refresh_token(new_token)
    )


# Thu hồi session qua store; gọi lặp lại vẫn thành công.
def revoke_session(db: Session, refresh_token: str) -> None:
    session = stores.one(db, "lock_auth_session_by_hash", hash=hash_refresh_token(refresh_token))
    if session is not None and session.revoked_at is None:
        stores.execute(db, "revoke_auth_session", id=session.id)
