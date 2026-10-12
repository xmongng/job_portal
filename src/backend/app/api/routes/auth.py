from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.dependencies.auth import AuthenticatedUser, CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# Dữ liệu người dùng gửi khi đăng ký; không cho chọn ADMIN.
class RegisterRequest(BaseModel):
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


# JSON trả về khi đăng nhập thành công.
class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # Thời hạn tính bằng giây.


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

    return TokenResponse(
        access_token=create_access_token(row["id"]),
        expires_in=get_settings().access_token_expire_minutes * 60,
    )


# FastAPI chạy get_current_user trước; chỉ user có token hợp lệ mới vào được route.
@router.get("/me", response_model=AuthenticatedUser)
def get_me(current_user: CurrentUser) -> AuthenticatedUser:
    return current_user
