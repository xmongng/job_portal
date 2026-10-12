from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hasher = PasswordHash.recommended()


# Register: chuyển mật khẩu gốc thành hash để lưu vào users.password_hash.
def hash_password(password: str) -> str:
    return password_hasher.hash(password)


# Login: kiểm tra mật khẩu nhập vào có khớp hash đã lưu không.
def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


# Tạo access token JWT có thời hạn cho tài khoản đã đăng nhập.
def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),  # ID tài khoản sở hữu token.
        "iat": now,  # Thời điểm cấp token.
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),  # Thời điểm hết hạn.
        "type": "access",  # Phân biệt mục đích sử dụng token.
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256",
    )
