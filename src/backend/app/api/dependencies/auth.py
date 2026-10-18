from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import text

from app.api.dependencies.database import DatabaseSession
from app.core.config import get_settings

# Đọc Authorization: Bearer <token>; tự xử lý lỗi khi thiếu token.
bearer_scheme = HTTPBearer(auto_error=False)


# Thông tin tài khoản đã xác thực, không chứa mật khẩu.
class AuthenticatedUser(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    status: str


# Dependency dùng chung cho các API yêu cầu đăng nhập.
def get_current_user(
    db: DatabaseSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AuthenticatedUser:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    settings = get_settings()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={
                "require": ["sub", "iat", "exp", "type", "sid"],
            },
        )

        if payload["type"] != "access":
            raise unauthorized

        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"])

    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise unauthorized

    row = (
        db.execute(
            text("SELECT * FROM public.get_session_user(:user_id, :session_id)"),
            {"user_id": user_id, "session_id": session_id},
        )
        .mappings()
        .one_or_none()
    )

    if row is None:
        raise unauthorized

    if row["status"] != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended",
        )

    return AuthenticatedUser.model_validate(row)


# Route khai báo CurrentUser sẽ nhận object do get_current_user trả về.
CurrentUser = Annotated[
    AuthenticatedUser,
    Depends(get_current_user),
]
