from functools import lru_cache
from pathlib import Path

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


@lru_cache
def get_settings() -> Settings:
    """Tạo Settings một lần rồi tái sử dụng trong suốt vòng đời process."""

    return Settings()
