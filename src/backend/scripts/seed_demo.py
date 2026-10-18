"""Tạo dữ liệu liên kết cho 17 bảng của database development rút gọn."""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid5

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.persistence import stores
from app.infrastructure.persistence.database import SessionLocal

NAMESPACE = UUID("5e2d293e-3330-4e89-a6be-382a66e2a41d")
EXPECTED_REVISION = "d927ac4106b8"
SAMPLE_SIZE = 5


def sample_id(table: str, number: int) -> UUID:
    """Sinh UUID ổn định để các lần dựng database có cùng ID mẫu."""
    return uuid5(NAMESPACE, f"job-portal-demo:{table}:{number}")


def digest(value: str) -> str:
    """Tạo giá trị giả giống hash token; không phải credential đăng nhập thật."""
    return hashlib.sha256(value.encode()).hexdigest()


def main() -> None:
    now = datetime.now(UTC)

    with SessionLocal.begin() as conn:
        context = stores.one(conn, "get_seed_context")
        database = context.database_name
        if database != "jobportal":
            raise RuntimeError(f"Refusing to seed unexpected database: {database}")

        revision = context.revision
        if revision != EXPECTED_REVISION:
            raise RuntimeError(f"Expected migration {EXPECTED_REVISION}, got {revision}")

        tables = {row.table_name: row.row_count for row in stores.many(conn, "get_seed_counts")}
        occupied = [table for table, count in tables.items() if count != 0]
        if occupied:
            raise RuntimeError("Refusing to seed nonempty tables: " + ", ".join(occupied))

        def add(table: str, **values: object) -> None:
            if table not in tables:
                raise ValueError("Unknown demo table")
            stores.execute(
                conn, "seed_" + table, json_fields=("education", "experience", "details"), **values
            )

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
                education=[
                    {
                        "school": f"Demo University {number}",
                        "major": "Computer Science",
                        "start_year": 2020,
                        "end_year": 2024,
                    }
                ],
                experience=[
                    {
                        "company": f"Previous Company {number}",
                        "position": "Developer",
                        "start_date": "2024-01-01",
                        "end_date": "2025-12-31",
                    }
                ],
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

        for number in range(1, SAMPLE_SIZE + 1):
            add(
                "job_status_history",
                id=sample_id("job_status_history", number),
                job_id=sample_id("jobs", number),
                actor_id=admin_id,
                from_status=None,
                to_status="PUBLISHED",
                note="Seed snapshot",
            )
            add(
                "application_status_history",
                id=sample_id("application_status_history", number),
                application_id=sample_id("applications", number),
                actor_id=admin_id,
                from_status=None,
                to_status="OFFER",
                note="Seed snapshot",
            )
            add(
                "audit_logs",
                id=sample_id("audit_logs", number),
                actor_id=admin_id,
                action="DEMO_SEEDED",
                resource_id=sample_id("jobs", number),
                details={},
            )

        counts = {row.table_name: row.row_count for row in stores.many(conn, "get_seed_counts")}
        expected = {name: (11 if name == "users" else SAMPLE_SIZE) for name in tables}
        if counts != expected:
            raise RuntimeError(f"Unexpected row counts: {counts}")

    print(f"Seeded {len(tables)} tables in {database} (5 rows each; users: 11).")


if __name__ == "__main__":
    main()
