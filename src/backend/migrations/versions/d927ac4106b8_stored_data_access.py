"""Đưa mọi thao tác dữ liệu API vào các store nhỏ có comment.

Revision ID: d927ac4106b8
Revises: c684d93ea201
"""

from pathlib import Path

from alembic import op

revision = "d927ac4106b8"
down_revision = "c684d93ea201"
branch_labels = None
depends_on = None
SQL_DIR = Path(__file__).resolve().parents[1] / "sql/stores_v1"


def upgrade() -> None:
    # JWT hiện kiểm tra session bằng get_session_user; bỏ store cũ không còn được gọi.
    op.execute("DROP FUNCTION IF EXISTS public.get_current_user(uuid)")
    for name in (*NAMES, "development"):
        op.execute((SQL_DIR / f"{name}.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute((SQL_DIR / "drop.sql").read_text(encoding="utf-8"))
    op.execute((SQL_DIR / "restore_legacy_current_user.sql").read_text(encoding="utf-8"))


NAMES = [
    "auth",
    "company",
    "job",
    "resume",
    "application",
    "session",
    "applicant",
    "skill",
    "interview",
    "offer",
    "notification",
]
