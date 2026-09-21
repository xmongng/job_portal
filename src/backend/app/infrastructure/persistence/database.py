from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Engine quản lý connection pool và tạo kết nối thật khi có truy vấn.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

# Factory tạo một Session độc lập cho mỗi request/use case.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db_session() -> Generator[Session, None, None]:
    """Cấp một Session cho request và luôn đóng Session sau khi xử lý xong."""

    with SessionLocal() as session:
        yield session
