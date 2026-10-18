"""Recruitment workflows through Week 6, with frozen SQL definitions.

Revision ID: c684d93ea201
Revises: 0c4b8405e072
"""

from pathlib import Path

from alembic import op

revision = "c684d93ea201"
down_revision = "0c4b8405e072"
branch_labels = None
depends_on = None
SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def run_sql(name: str) -> None:
    op.execute((SQL_DIR / name).read_text(encoding="utf-8"))


def upgrade() -> None:
    run_sql("week6_schema.sql")
    # Older versions returned a different job-detail shape; recreate its signature safely.
    op.execute("DROP FUNCTION IF EXISTS public.get_public_job(uuid)")
    for name in (
        "auth",
        "company",
        "job",
        "applicant",
        "session",
        "skill",
    ):
        run_sql(f"week6_{name}.sql")


def downgrade() -> None:
    # Refuse lossy rollback when the old schema cannot represent current business data.
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM public.jobs WHERE status IN ('PENDING_APPROVAL','REJECTED'))
         OR EXISTS(SELECT 1 FROM public.applications WHERE status='SCREENING')
         OR EXISTS(SELECT 1 FROM public.offers WHERE status IN ('EXPIRED','CANCELLED'))
         OR EXISTS(SELECT 1 FROM public.offers GROUP BY application_id HAVING count(*)>1) THEN
        RAISE EXCEPTION 'Cannot downgrade: Week 4-6 data requires the new schema';
      END IF;
    END $$;""")
    run_sql("week6_drop_functions.sql")
    op.execute(
        "DROP TABLE public.audit_logs, public.application_status_history, public.job_status_history"
    )
    op.execute("ALTER TABLE public.applications DROP COLUMN resume_snapshot")
    op.execute("ALTER TABLE public.interviews DROP COLUMN duration_minutes")
    op.execute(
        "ALTER TABLE public.notifications DROP COLUMN email_sent_at, DROP COLUMN email_attempts, DROP COLUMN email_error"
    )
    op.execute("DROP INDEX public.uq_resume_default_applicant")
    op.execute("DROP INDEX public.uq_offer_active_application")
    op.execute("DROP INDEX public.ix_applications_job_status")
    op.execute("DROP INDEX public.ix_notifications_user_created")
    op.execute(
        "ALTER TABLE public.offers ADD CONSTRAINT uq_offers_application_id UNIQUE(application_id)"
    )
    op.execute("ALTER TABLE public.jobs DROP CONSTRAINT ck_jobs_nonnegative_salary_max")
    for table, values in (
        ("jobs", "'DRAFT','PUBLISHED','CLOSED'"),
        ("applications", "'APPLIED','INTERVIEW','OFFER','HIRED','REJECTED','WITHDRAWN'"),
        ("offers", "'DRAFT','SENT','ACCEPTED','REJECTED'"),
    ):
        op.execute(f"ALTER TABLE public.{table} DROP CONSTRAINT ck_{table}_valid_status")
        op.execute(
            f"ALTER TABLE public.{table} ADD CONSTRAINT ck_{table}_valid_status CHECK(status IN ({values}))"
        )
