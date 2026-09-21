from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.infrastructure.persistence import models  # noqa: F401
from app.infrastructure.persistence.base import Base

config = context.config

# Dùng cấu hình logging trong alembic.ini khi Alembic chạy bằng CLI.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Không ghi credential vào alembic.ini; Alembic dùng cùng Settings với API.
# Ký tự % phải escape vì ConfigParser dùng nó cho nội suy biến.
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Sinh SQL migration mà không cần mở kết nối trực tiếp tới PostgreSQL."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Mở kết nối PostgreSQL và áp dụng migration trong transaction."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Alembic quyết định chế độ dựa trên câu lệnh CLI hiện tại.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
