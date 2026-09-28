"""Tạo dữ liệu liên kết cho 14 bảng của database development rút gọn."""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import create_engine, func, select, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.infrastructure.persistence import models  # noqa: F401
from app.infrastructure.persistence.base import Base

NAMESPACE = UUID("5e2d293e-3330-4e89-a6be-382a66e2a41d")
EXPECTED_REVISION = "0c4b8405e072"
SAMPLE_SIZE = 5


def sample_id(table: str, number: int) -> UUID:
    """Sinh UUID ổn định để các lần dựng database có cùng ID mẫu."""
    return uuid5(NAMESPACE, f"job-portal-demo:{table}:{number}")


def digest(value: str) -> str:
    """Tạo giá trị giả giống hash token; không phải credential đăng nhập thật."""
    return hashlib.sha256(value.encode()).hexdigest()


def main() -> None:
    engine = create_engine(get_settings().database_url)
    tables = Base.metadata.tables
    now = datetime.now(UTC)

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

        admin_id = sample_id("users", 11)
        add(
            "users",
            id=admin_id,
            email="admin@demo.invalid",
            password_hash="!demo-no-login!",
            full_name="Demo Admin",
            role="ADMIN",
        )

        for number in range(1, SAMPLE_SIZE + 1):
            applicant_user_id = sample_id("users", number)
            recruiter_user_id = sample_id("users", number + SAMPLE_SIZE)
            applicant_id = sample_id("applicants", number)
            company_id = sample_id("companies", number)
            skill_id = sample_id("skills", number)
            job_id = sample_id("jobs", number)
            resume_id = sample_id("resumes", number)
            application_id = sample_id("applications", number)

            add(
                "users",
                id=applicant_user_id,
                email=f"applicant{number}@demo.invalid",
                password_hash="!demo-no-login!",
                full_name=f"Demo Applicant {number}",
                role="APPLICANT",
            )
            add(
                "users",
                id=recruiter_user_id,
                email=f"recruiter{number}@demo.invalid",
                password_hash="!demo-no-login!",
                full_name=f"Demo Recruiter {number}",
                role="RECRUITER",
            )
            add(
                "auth_sessions",
                id=sample_id("auth_sessions", number),
                user_id=applicant_user_id,
                refresh_token_hash=digest(f"demo-session-{number}"),
                expires_at=now - timedelta(days=1),
                revoked_at=now - timedelta(days=1),
            )
            add(
                "companies",
                id=company_id,
                name=f"Demo Company {number}",
                description="Synthetic company for local development",
                industry="Software",
                location=f"Demo City {number}",
                verification_status="VERIFIED",
            )
            add(
                "company_memberships",
                id=sample_id("company_memberships", number),
                company_id=company_id,
                user_id=recruiter_user_id,
                membership_role="OWNER",
            )
            add(
                "applicants",
                id=applicant_id,
                user_id=applicant_user_id,
                headline=f"Backend Developer {number}",
                summary="Demo applicant profile",
                location=f"Demo City {number}",
                education=[{"school": f"Demo University {number}", "degree": "Bachelor"}],
                experience=[{"company": f"Previous Company {number}", "role": "Developer"}],
                desired_salary=25_000_000,
            )
            add("skills", id=skill_id, name=f"Demo Skill {number}")
            add("applicant_skills", applicant_id=applicant_id, skill_id=skill_id)
            add(
                "jobs",
                id=job_id,
                company_id=company_id,
                created_by=recruiter_user_id,
                title=f"Demo Python Developer {number}",
                description="Synthetic job for local development",
                requirements=f"Demo Skill {number}",
                location=f"Demo City {number}",
                category="Software Development",
                employment_type="FULL_TIME",
                salary_min=20_000_000,
                salary_max=30_000_000,
                deadline=now + timedelta(days=30),
                status="PUBLISHED",
            )
            add("job_skills", job_id=job_id, skill_id=skill_id)
            add(
                "resumes",
                id=resume_id,
                applicant_id=applicant_id,
                title=f"Demo Resume {number}",
                storage_key=f"demo/resume-{number}.pdf",
                original_name=f"resume-{number}.pdf",
                mime_type="application/pdf",
                size_bytes=1000 + number,
                is_default=True,
            )
            add(
                "applications",
                id=application_id,
                job_id=job_id,
                applicant_id=applicant_id,
                resume_id=resume_id,
                cover_letter="Demo cover letter",
                recruiter_note="Demo internal note",
                status="OFFER",
            )
            add(
                "interviews",
                id=sample_id("interviews", number),
                application_id=application_id,
                round_number=1,
                scheduled_at=now - timedelta(days=2),
                mode="ONLINE",
                location_or_url=f"https://example.invalid/interview/{number}",
                status="COMPLETED",
                result="PASS",
                feedback="Demo feedback",
            )
            add(
                "offers",
                id=sample_id("offers", number),
                application_id=application_id,
                salary=25_000_000,
                start_date=(now + timedelta(days=30)).date(),
                response_deadline=now + timedelta(days=14),
                terms="Demo offer terms",
                status="SENT",
            )
            add(
                "notifications",
                id=sample_id("notifications", number),
                user_id=applicant_user_id,
                title="Demo offer",
                body="You received a demo offer",
                resource_type="APPLICATION",
                resource_id=application_id,
            )

        counts = {
            table.name: conn.scalar(select(func.count()).select_from(table))
            for table in tables.values()
        }
        expected = {name: (11 if name == "users" else SAMPLE_SIZE) for name in tables}
        if counts != expected:
            raise RuntimeError(f"Unexpected row counts: {counts}")

    print(f"Seeded {len(tables)} tables in {database} (5 rows each; users: 11).")


if __name__ == "__main__":
    main()
