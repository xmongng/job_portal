import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import get_settings

password_hasher = PasswordHash.recommended()


# Register: chuyển mật khẩu gốc thành hash để lưu vào users.password_hash.
def hash_password(password: str) -> str:
    return password_hasher.hash(password)


# Login: kiểm tra mật khẩu nhập vào có khớp hash đã lưu không.
def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password, password_hash)
    except (UnknownHashError, ValueError):
        # Demo/legacy invalid hashes must fail login rather than crash the API.
        return False


# Tạo access token JWT có thời hạn cho tài khoản đã đăng nhập.
def create_access_token(user_id: UUID, session_id: UUID | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),  # ID tài khoản sở hữu token.
        "iat": now,  # Thời điểm cấp token.
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),  # Thời điểm hết hạn.
        "type": "access",  # Phân biệt mục đích sử dụng token.
    }

    if session_id is not None:
        payload["sid"] = str(session_id)

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256",
    )


# Tạo refresh token ngẫu nhiên để trả cho client khi đăng nhập.
def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)


# Hash refresh token trước khi lưu hoặc tìm kiếm trong auth_sessions.
# Không lưu refresh token gốc trong database.
def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
