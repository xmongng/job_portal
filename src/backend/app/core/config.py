from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Định nghĩa và kiểm tra các biến cấu hình mà backend cần sử dụng."""

    # Đọc biến môi trường của hệ điều hành và file src/backend/.env.
    # extra="ignore" cho phép .env chứa thêm JWT/SMTP mà class này chưa dùng tới.
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(alias="DATABASE_URL")
    # Khóa ký JWT đọc từ .env; access token mặc định hết hạn sau 30 phút.
    jwt_secret: str = Field(alias="JWT_SECRET", min_length=32)
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES", ge=1)

    # Refresh token mặc định có thời hạn 7 ngày.
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
        ge=1,
    )

    file_storage_path: Path = Field(
        default=BACKEND_DIR / "private-resumes", alias="FILE_STORAGE_PATH"
    )
    max_resume_bytes: int = Field(default=5 * 1024 * 1024, ge=1, le=5 * 1024 * 1024)
    ai_provider: Literal["none", "gemini"] = "none"
    ai_api_key: str = ""
    ai_model: str = Field(default="", pattern=r"^[A-Za-z0-9._-]*$")
    ai_timeout_seconds: float = Field(default=10, gt=0, le=30)
    cors_origins: list[str] = []
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    auth_rate_limit_per_minute: int = Field(default=30, ge=1)
    ai_rate_limit_per_minute: int = Field(default=10, ge=1)
    smtp_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "no-reply@jobportal.local"


@lru_cache
def get_settings() -> Settings:
    """Tạo Settings một lần rồi tái sử dụng trong suốt vòng đời process."""

    return Settings()
