"""Recommendation, admin moderation and aggregate reports.

Revision ID: e731ba6208c4
Revises: d927ac4106b8
"""

from pathlib import Path

from alembic import op

revision = "e731ba6208c4"
down_revision = "d927ac4106b8"
branch_labels = None
depends_on = None
SQL_DIR = Path(__file__).resolve().parents[1] / "sql/week7"


def upgrade() -> None:
    for name in ("recommendation", "admin", "report"):
        op.execute((SQL_DIR / f"{name}.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute((SQL_DIR / "drop.sql").read_text(encoding="utf-8"))
