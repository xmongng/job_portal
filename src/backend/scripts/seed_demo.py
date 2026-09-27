"""Insert connected demo rows into an empty local Job Portal database.

Usage: from src/backend, run ``.venv/bin/python scripts/seed_demo.py``.
This is deliberately one-shot: it refuses to run if any business table has data.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import create_engine, func, select, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.infrastructure.persistence import models  # noqa: F401
from app.infrastructure.persistence.base import Base

NAMESPACE = UUID("5e2d293e-3330-4e89-a6be-382a66e2a41d")
EXPECTED_REVISION = "0b3c0d074786"
SAMPLE_SIZE = 5


def sample_id(table: str, number: int) -> UUID:
    return uuid5(NAMESPACE, f"job-portal-demo:{table}:{number}")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def main() -> None:
    engine = create_engine(get_settings().database_url)
    tables = Base.metadata.tables
    now = datetime.now(UTC)
    tomorrow = now + timedelta(days=1)

    with engine.begin() as conn:
        database = conn.execute(text("SELECT current_database()")).scalar_one()
        if database != "jobportal":
            raise RuntimeError(f"Refusing to seed unexpected database: {database}")
        revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        if revision != EXPECTED_REVISION:
            raise RuntimeError(f"Expected migration {EXPECTED_REVISION}, got {revision}")
        occupied = [
            table.name
            for table in tables.values()
            if conn.scalar(select(func.count()).select_from(table)) != 0
        ]
        if occupied:
            raise RuntimeError("Refusing to seed nonempty tables: " + ", ".join(occupied))

        def add(table: str, **values: object) -> None:
            conn.execute(tables[table].insert().values(**values))

        admin = sample_id("users", 11)
        add(
            "users",
            id=admin,
            email="admin@demo.invalid",
            password_hash="!demo-no-login!",
            role="ADMIN",
            full_name="Demo Admin",
        )

        for i in range(1, SAMPLE_SIZE + 1):
            applicant_user = sample_id("users", i)
            recruiter_user = sample_id("users", i + SAMPLE_SIZE)
            applicant = sample_id("applicants", i)
            company = sample_id("companies", i)
            job = sample_id("jobs", i)
            resume = sample_id("resumes", i)
            application = sample_id("applications", i)
            location = sample_id("locations", i)
            category = sample_id("job_categories", i)
            skill = sample_id("skills", i)
            notification = sample_id("notifications", i)
            document = sample_id("cv_documents", i)

            add("locations", id=location, code=f"DEMO-{i:02d}", name=f"Demo City {i}")
            add("job_categories", id=category, name=f"Demo Category {i}")
            add("skills", id=skill, name=f"Demo Skill {i}", normalized_name=f"demo-skill-{i}")
            add(
                "users",
                id=applicant_user,
                email=f"applicant{i}@demo.invalid",
                password_hash="!demo-no-login!",
                role="APPLICANT",
                full_name=f"Demo Applicant {i}",
            )
            add(
                "users",
                id=recruiter_user,
                email=f"recruiter{i}@demo.invalid",
                password_hash="!demo-no-login!",
                role="RECRUITER",
                full_name=f"Demo Recruiter {i}",
            )
            add(
                "auth_sessions",
                id=sample_id("auth_sessions", i),
                user_id=applicant_user,
                refresh_token_hash=digest(f"demo-session-{i}"),
                expires_at=now - timedelta(days=1),
                revoked_at=now - timedelta(days=1),
            )
            add(
                "account_tokens",
                id=sample_id("account_tokens", i),
                user_id=applicant_user,
                purpose="VERIFY_EMAIL",
                token_hash=digest(f"demo-token-{i}"),
                expires_at=now - timedelta(days=1),
                consumed_at=now - timedelta(days=1),
            )
            add(
                "applicants",
                id=applicant,
                user_id=applicant_user,
                headline=f"Demo backend developer {i}",
                location_id=location,
                preferred_location_id=location,
                years_experience=i,
                preferred_work_mode="REMOTE",
                preferred_employment_type="FULL_TIME",
            )
            add(
                "applicant_educations",
                id=sample_id("applicant_educations", i),
                applicant_id=applicant,
                institution=f"Demo University {i}",
                degree="Bachelor",
                field_of_study="Computer Science",
                start_date=date(2018, 9, 1),
                end_date=date(2022, 6, 30),
            )
            add(
                "applicant_experiences",
                id=sample_id("applicant_experiences", i),
                applicant_id=applicant,
                company_name=f"Demo Previous Employer {i}",
                job_title="Software Developer",
                start_date=date(2022, 7, 1),
                end_date=date(2024, 7, 1),
            )
            add("applicant_skills", applicant_id=applicant, skill_id=skill)
            add(
                "companies",
                id=company,
                name=f"Demo Company {i}",
                registration_number=f"DEMO-REG-{i:04d}",
                description="Synthetic company for local development only",
                industry="Software",
                size_band="11_50",
                address=f"Demo Address {i}",
                location_id=location,
                verification_status="VERIFIED",
                reviewed_by=admin,
                reviewed_at=now,
                created_by=recruiter_user,
            )
            add(
                "company_memberships",
                id=sample_id("company_memberships", i),
                company_id=company,
                user_id=recruiter_user,
                membership_role="OWNER",
            )
            add(
                "company_invitations",
                id=sample_id("company_invitations", i),
                company_id=company,
                email=f"invite{i}@demo.invalid",
                invited_by=recruiter_user,
                token_hash=digest(f"demo-invite-{i}"),
                status="EXPIRED",
                expires_at=now - timedelta(days=1),
            )
            add(
                "cv_documents",
                id=document,
                applicant_id=applicant,
                title=f"Demo CV Draft {i}",
                template_code="BASIC_V1",
                content={"demo": True, "note": "Synthetic draft; not a real CV"},
            )
            add(
                "resumes",
                id=resume,
                applicant_id=applicant,
                source="UPLOAD",
                title=f"Demo Resume {i}",
                storage_key=f"demo/missing/resume-{i}.pdf",
                original_name=f"demo-resume-{i}.pdf",
                mime_type="application/pdf",
                size_bytes=1000 + i,
                sha256=digest(f"demo-file-{i}"),
                is_default=True,
            )
            add(
                "jobs",
                id=job,
                company_id=company,
                created_by=recruiter_user,
                title=f"Demo Python Developer {i}",
                description="Synthetic job for local development only",
                requirements="Demo Python skill",
                category_id=category,
                location_id=location,
                employment_type="FULL_TIME",
                work_mode="REMOTE",
                seniority="JUNIOR",
                salary_min=20_000_000,
                salary_max=30_000_000,
                is_negotiable=False,
                deadline=now + timedelta(days=30),
                status="PUBLISHED",
                published_at=now,
            )
            add("job_skills", job_id=job, skill_id=skill)
            add(
                "job_status_history",
                id=sample_id("job_status_history", i),
                job_id=job,
                from_status="PENDING_APPROVAL",
                to_status="PUBLISHED",
                changed_by=admin,
                actor_type="USER",
                reason="Demo approval",
            )
            add(
                "applications",
                id=application,
                job_id=job,
                applicant_id=applicant,
                resume_id=resume,
                contact_name=f"Demo Applicant {i}",
                contact_email=f"applicant{i}@demo.invalid",
                contact_phone="0000000000",
                status="OFFER",
            )
            add(
                "application_status_history",
                id=sample_id("application_status_history", i),
                application_id=application,
                from_status="INTERVIEW",
                to_status="OFFER",
                changed_by=recruiter_user,
                actor_type="USER",
                reason="Demo progression",
            )
            add(
                "application_notes",
                id=sample_id("application_notes", i),
                application_id=application,
                author_id=recruiter_user,
                content=f"Synthetic note for application {i}",
            )
            add(
                "interviews",
                id=sample_id("interviews", i),
                application_id=application,
                round_number=1,
                starts_at=now - timedelta(days=2),
                ends_at=now - timedelta(days=2) + timedelta(hours=1),
                mode="ONLINE",
                meeting_url=f"https://example.invalid/interview/{i}",
                interviewer_name=f"Demo Recruiter {i}",
                status="COMPLETED",
                result="PASS",
                created_by=recruiter_user,
            )
            add(
                "offers",
                id=sample_id("offers", i),
                application_id=application,
                sequence_number=1,
                salary=25_000_000,
                start_date=tomorrow.date() + timedelta(days=30),
                response_deadline=now + timedelta(days=14),
                terms="Synthetic draft offer",
                status="DRAFT",
                created_by=recruiter_user,
            )
            add(
                "notifications",
                id=notification,
                user_id=applicant_user,
                event_key=f"demo:offer:{i}",
                type="DEMO_OFFER",
                title="Demo notification",
                body="Synthetic notification; no message was sent",
                resource_type="APPLICATION",
                resource_id=application,
                read_at=now,
            )
            add(
                "email_deliveries",
                id=sample_id("email_deliveries", i),
                user_id=applicant_user,
                notification_id=notification,
                dedup_key=f"demo-email-{i}",
                recipient=f"applicant{i}@demo.invalid",
                template_code="DEMO_ONLY",
                payload_ciphertext=b"demo-placeholder-not-real-ciphertext",
                status="SENT",
                next_attempt_at=now - timedelta(days=1),
                sent_at=now,
            )
            add(
                "audit_logs",
                id=sample_id("audit_logs", i),
                actor_id=admin,
                action="DEMO_SEED",
                entity_type="JOB",
                entity_id=job,
                request_id=sample_id("audit_requests", i),
                outcome="SUCCESS",
                metadata={"demo": True},
            )
            add(
                "security_rate_windows",
                scope="LOGIN",
                subject_hash=digest(f"demo-rate-{i}"),
                window_start=now - timedelta(days=2),
                request_count=0,
            )
            add(
                "ai_operations",
                id=sample_id("ai_operations", i),
                requested_by=applicant_user,
                feature="MATCH_EXPLANATION",
                applicant_id=applicant,
                job_id=job,
                input_hash=digest(f"demo-ai-{i}"),
                provider="DEMO",
                model="demo-only",
                prompt_version="demo-v1",
                status="SUCCEEDED",
                output={"summary": "Synthetic result; no AI request was made"},
                input_tokens=0,
                output_tokens=0,
                expires_at=now - timedelta(days=1),
            )
            add(
                "ai_rate_windows",
                user_id=applicant_user,
                feature="MATCH_EXPLANATION",
                window_start=now - timedelta(days=2),
                request_count=0,
                reserved_tokens=0,
            )

        counts = {
            table.name: conn.scalar(select(func.count()).select_from(table))
            for table in tables.values()
        }
        expected = {table: (11 if table == "users" else SAMPLE_SIZE) for table in tables}
        if counts != expected:
            raise RuntimeError(f"Unexpected row counts: {counts}")

    print(f"Seeded {len(tables)} business tables in {database} (5 rows each; users: 11).")
    print("Demo emails use .invalid; credentials cannot log in; CV file paths are placeholders.")


if __name__ == "__main__":
    main()
