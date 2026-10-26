"""Real PostgreSQL workflow. Each test rolls back and stores PDFs in a temp folder."""

from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import uuid4

from pypdf import PdfWriter
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.infrastructure.persistence import stores


# Covers three roles, privacy, state transitions, moderation, reports and rule/AI fallback.
def test_full_recruitment_and_week7(integration_client):
    client, connection = integration_client
    password = "TestPassword123!"
    suffix = uuid4().hex

    def call(method, path, status=200, token=None, **kwargs):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        result = client.request(method, "/api" + path, headers=headers, **kwargs)
        assert result.status_code == status, (method, path, status, result.status_code, result.text)
        return (
            result.json()
            if "application/json" in result.headers.get("content-type", "")
            else result.content
        )

    def account(role):
        email = f"{role.lower()}-{uuid4().hex}@example.com"
        row = call(
            "POST",
            "/auth/register",
            201,
            json={"email": email, "password": password, "full_name": "Test " + role, "role": role},
        )
        login = call("POST", "/auth/login", json={"email": email, "password": password})
        return row, login

    with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
        admin_email = f"admin-{suffix}@example.com"
        stores.execute(
            db,
            "insert_admin",
            email=admin_email,
            password_hash=hash_password(password),
            full_name="Admin",
            role="ADMIN",
        )
        db.commit()
    admin = call("POST", "/auth/login", json={"email": admin_email, "password": password})[
        "access_token"
    ]
    applicant, auth = account("APPLICANT")
    token = auth["access_token"]
    _recruiter, rauth = account("RECRUITER")
    rtoken = rauth["access_token"]
    _outsider, oauth = account("RECRUITER")
    otoken = oauth["access_token"]
    call(
        "POST",
        "/auth/register",
        409,
        json={
            "email": applicant["email"],
            "password": password,
            "full_name": "Duplicate",
            "role": "APPLICANT",
        },
    )
    call("GET", "/applicants/me", 401)
    call("GET", "/applicants/me", 403, token=rtoken)
    call(
        "PUT",
        "/applicants/me",
        token=token,
        json={"headline": "Python Developer", "location": "HCM", "desired_salary": "20000000"},
    )
    skill = call("POST", "/skills", 201, token=admin, json={"name": "Python-" + suffix})["id"]
    call("PUT", "/applicants/me/skills", token=token, json={"skill_ids": [skill]})
    call("PUT", "/applicants/me/skills", 422, token=token, json={"skill_ids": [str(uuid4())]})
    company = call(
        "POST",
        "/companies",
        201,
        token=rtoken,
        json={"name": "Test Company", "industry": "Software", "location": "HCM"},
    )["id"]
    call("POST", f"/admin/companies/{company}/review", token=admin, json={"decision": "VERIFIED"})
    job = call(
        "POST",
        f"/companies/{company}/jobs",
        201,
        token=rtoken,
        json={
            "title": "Python developer",
            "description": "Build services",
            "location": "HCM",
            "category": "Software",
            "employment_type": "FULL_TIME",
            "salary_min": "20000000",
            "salary_max": "30000000",
            "deadline": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
            "skill_ids": [skill],
        },
    )["id"]
    call("POST", f"/jobs/{job}/approve", 403, token=rtoken)
    call("POST", f"/jobs/{job}/submit", token=rtoken)
    call("POST", f"/jobs/{job}/approve", token=admin)
    call("GET", f"/recruiter/jobs/{job}", 403, token=otoken)
    matches = call("GET", "/recommendations", token=token)
    match = next(m for m in matches if m["id"] == job)
    assert match["score"] == 100 and match["skill_score"] == 70
    explanation = call("POST", f"/ai/jobs/{job}/explain", token=token)
    assert explanation["source"] == "rules" and explanation["match"]["score"] == 100
    call("GET", "/recommendations", 403, token=rtoken)
    draft = call(
        "POST",
        "/ai/job-description",
        token=rtoken,
        json={
            "title": "Developer",
            "category": "Software",
            "location": "HCM",
            "skills": ["Python"],
        },
    )
    assert draft["requires_review"] and draft["source"] == "rules"
    call(
        "POST",
        "/ai/job-description",
        403,
        token=token,
        json={"title": "Developer", "category": "Software", "location": "HCM"},
    )
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    stream = BytesIO()
    writer.write(stream)
    call(
        "POST",
        "/resumes",
        422,
        token=token,
        data={"title": "Bad"},
        files={"file": ("bad.pdf", b"bad", "application/pdf")},
    )
    resume = call(
        "POST",
        "/resumes",
        201,
        token=token,
        data={"title": "My CV"},
        files={"file": ("cv.pdf", stream.getvalue(), "application/pdf")},
    )["id"]
    application = call(
        "POST", "/applications", 201, token=token, json={"job_id": job, "resume_id": resume}
    )["id"]
    call("POST", "/applications", 409, token=token, json={"job_id": job, "resume_id": resume})
    call("DELETE", f"/resumes/{resume}", 409, token=token)
    call("GET", f"/applications/{application}", 403, token=otoken)
    call(
        "PUT",
        f"/applications/{application}/note",
        token=rtoken,
        json={"note": "Private recruiter note"},
    )
    own = call("GET", f"/applications/{application}", token=token)
    assert "recruiter_note" not in own and "storage_key" not in own["resume_snapshot"]
    call(
        "POST",
        f"/applications/{application}/status",
        409,
        token=rtoken,
        json={"status": "INTERVIEW"},
    )
    for status in ["SCREENING", "INTERVIEW"]:
        call("POST", f"/applications/{application}/status", token=rtoken, json={"status": status})
    scheduled = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    interview = call(
        "POST",
        f"/applications/{application}/interviews",
        201,
        token=rtoken,
        json={
            "round_number": 1,
            "scheduled_at": scheduled,
            "duration_minutes": 60,
            "mode": "ONLINE",
            "location_or_url": "https://example.com/interview",
        },
    )["id"]
    call(
        "POST",
        f"/applications/{application}/interviews",
        409,
        token=rtoken,
        json={
            "round_number": 2,
            "scheduled_at": scheduled,
            "mode": "ONLINE",
            "location_or_url": "https://example.com/interview",
        },
    )
    call("POST", f"/interviews/{interview}/result", 409, token=rtoken, json={"result": "PASS"})
    # Fixture clock adjustment only; there is no API that bypasses the scheduled time.
    connection.execute(
        text("UPDATE interviews SET scheduled_at=now()-interval '2 hours' WHERE id=:id"),
        {"id": interview},
    )
    call(
        "POST",
        f"/interviews/{interview}/result",
        token=rtoken,
        json={"result": "PASS", "feedback": "Private feedback"},
    )
    assert "feedback" not in call("GET", f"/applications/{application}/interviews", token=token)[0]
    offer = call(
        "POST",
        f"/applications/{application}/offers",
        201,
        token=rtoken,
        json={
            "salary": "25000000",
            "start_date": (datetime.now(UTC) + timedelta(days=30)).date().isoformat(),
            "response_deadline": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        },
    )["id"]
    call("GET", f"/offers/{offer}", 404, token=token)
    call("POST", f"/offers/{offer}/send", token=rtoken)
    call("POST", f"/offers/{offer}/accept", token=token)
    assert call("GET", f"/applications/{application}", token=token)["status"] == "HIRED"
    call("POST", f"/applications/{application}/withdraw", 409, token=token)
    notices = call("GET", "/notifications", token=token)
    call("PUT", f"/notifications/{notices[0]['id']}/read", token=token)
    report = call("GET", f"/reports/summary?company_id={company}", token=rtoken)
    assert report["counts"]["applications"] == 1
    call("GET", f"/reports/summary?company_id={company}", 403, token=otoken)
    call("GET", "/reports/summary", 403, token=token)
    assert b"summary,jobs" in call("GET", "/reports/export.csv", token=admin)
    call("GET", "/admin/users", 403, token=token)
    assert all("password_hash" not in user for user in call("GET", "/admin/users", token=admin))
    call("PUT", f"/admin/companies/{company}/status", token=admin, json={"status": "SUSPENDED"})
    call("GET", f"/jobs/{job}", 404)
    call("GET", f"/recruiter/jobs/{job}", 403, token=rtoken)
    call("PUT", f"/admin/companies/{company}/status", token=admin, json={"status": "ACTIVE"})
    call("PUT", f"/admin/users/{applicant['id']}/status", token=admin, json={"status": "SUSPENDED"})
    call("GET", "/auth/me", 401, token=token)
    call("PUT", f"/admin/users/{applicant['id']}/status", token=admin, json={"status": "ACTIVE"})
    call("GET", "/auth/me", 401, token=token)
    rotated = call("POST", "/auth/refresh", json={"refresh_token": rauth["refresh_token"]})
    call("POST", "/auth/refresh", 401, json={"refresh_token": rauth["refresh_token"]})
    call("POST", "/auth/logout", 204, json={"refresh_token": rotated["refresh_token"]})
    call("GET", "/auth/me", 401, token=rotated["access_token"])
    call("GET", "/admin/audit-logs", token=admin)
