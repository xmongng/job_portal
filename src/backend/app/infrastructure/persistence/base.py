from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Tên constraint ổn định giúp migration Alembic dễ đọc và dễ thay đổi về sau.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Lớp cha mà mọi SQLAlchemy model của dự án phải kế thừa."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
