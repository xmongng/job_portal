from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.dependencies.auth import AuthenticatedUser, CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.application.auth.sessions import revoke_session, rotate_session
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# Dữ liệu người dùng gửi khi đăng ký; không cho chọn ADMIN.
class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr  # Kiểm tra email đúng định dạng.
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)
    role: Literal["APPLICANT", "RECRUITER"] = "APPLICANT"  # Chỉ nhận hai role này.


# Dữ liệu trả về; không chứa mật khẩu hoặc password_hash.
class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str


# JSON người dùng gửi để đăng nhập.
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# JSON trả về khi login hoặc refresh thành công.
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # Thời hạn access token, tính bằng giây.


# Hash mật khẩu, gọi store tạo tài khoản rồi commit transaction.
# response_model định nghĩa JSON trả về; đăng ký thành công trả HTTP 201.
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DatabaseSession) -> UserResponse:
    full_name = payload.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=422, detail="Full name must not be empty")

    try:
        row = (
            db.execute(
                text(
                    "Select * from public.register_user(:email, :password_hash, :full_name, :role)"
                ),
                {
                    "email": str(payload.email).strip().lower(),
                    "password_hash": hash_password(payload.password),  # Chỉ lưu hash mật khẩu.
                    "full_name": full_name,
                    "role": payload.role,
                },
            )
            .mappings()
            .one()
        )  # Đọc theo tên cột và yêu cầu kết quả có đúng một dòng.

        result = UserResponse.model_validate(row)  # Kiểm tra dữ liệu theo DTO trả về.
        db.commit()  # Xác nhận lưu tài khoản vào database.
        return result

    except IntegrityError as exc:  # Lỗi ràng buộc database, ví dụ email trùng.
        db.rollback()  # Hủy thay đổi của transaction bị lỗi.
        # Đọc mã lỗi PostgreSQL; 23505 là vi phạm ràng buộc duy nhất (unique).
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            ) from exc  # Giữ liên kết với lỗi database gốc khi trả lỗi HTTP.
        raise  # Lỗi ràng buộc khác: ném lại để backend xử lý.


# Lấy tài khoản, kiểm tra mật khẩu và trạng thái rồi cấp access token.
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DatabaseSession) -> TokenResponse:
    row = (
        db.execute(
            text("SELECT * FROM public.get_user_for_login(:email)"),
            {"email": str(payload.email).strip().lower()},
        )
        .mappings()
        .one_or_none()
    )

    # Dùng cùng thông báo cho email không tồn tại và mật khẩu sai.
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Tài khoản bị khóa không được đăng nhập.
    if row["status"] != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended",
        )

    settings = get_settings()
    refresh_token = create_refresh_token()
    session = (
        db.execute(
            text("SELECT * FROM public.create_auth_session(:user_id, :hash, :expires)"),
            {
                "user_id": row["id"],
                "hash": hash_refresh_token(refresh_token),
                "expires": datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            },
        )
        .mappings()
        .one()
    )
    result = TokenResponse(
        access_token=create_access_token(row["id"], session["id"]),
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
    db.commit()
    return result


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=256)


# Đổi refresh token nguyên tử; request dùng lại token cũ sẽ nhận 401.
@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: DatabaseSession) -> TokenResponse:
    token = create_refresh_token()
    session = rotate_session(db, payload.refresh_token, token)
    result = TokenResponse(
        access_token=create_access_token(session.user_id, session.id),
        refresh_token=token,
        expires_in=get_settings().access_token_expire_minutes * 60,
    )
    db.commit()
    return result


# Logout idempotent; JWT thuộc phiên bị thu hồi sẽ bị từ chối ngay.
@router.post("/logout", status_code=204)
def logout(payload: RefreshRequest, db: DatabaseSession) -> Response:
    revoke_session(db, payload.refresh_token)
    db.commit()
    return Response(status_code=204)


# FastAPI chạy get_current_user trước; chỉ user có token hợp lệ mới vào được route.
@router.get("/me", response_model=AuthenticatedUser)
def get_me(current_user: CurrentUser) -> AuthenticatedUser:
    return current_user
