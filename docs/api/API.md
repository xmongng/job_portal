# API through Week 6

Base URL local: `http://127.0.0.1:8000`. Swagger: `/docs`.

See [backend code guide](../architecture/BACKEND_GUIDE.md) and [Postman workflow](../flows/week6-postman.md).

Run `alembic upgrade head` after installing dependencies; the migration installs all SQL functions. Existing access tokens without a session ID require login again.

- Login returns `access_token`, `refresh_token`, `token_type`, `expires_in`.
- Refresh rotates the refresh token once while retaining the absolute session expiry (default 7 days).
- Logout revokes the session and immediately invalidates its access tokens. Use the latest refresh token.
- Other authenticated requests use `Authorization: Bearer <access_token>`.
- No endpoint allows public registration as ADMIN; use `scripts/create_admin.py`.
- UUID/body errors return 422; missing/invalid token 401; wrong role/resource 403 (private CV owner mismatch 404); resource conflicts/state transitions/duplicates 409.
- Paginated lists use `limit` (1–100) and `offset` (>=0); company public lists retain their existing fixed 20-record limit.
- CV uploads use multipart `title` + `file`, PDF only, maximum 5 MiB. Files and snapshots remain private.
- Applicants never receive recruiter notes, internal interview feedback or filesystem keys.
- Writes, history and in-app notifications commit together. Database constraints and locks protect concurrent operations.
- Company membership is at most one company per recruiter. Only OWNER manages company fields/members; MEMBER manages recruiting. Adding members uses an existing active recruiter account; invitation tokens are outside scope.
- Interviews cannot overlap for the same company/applicant; results can only be recorded once the scheduled time arrives.
- Offers past their deadline cannot be accepted. `is_expired` reflects elapsed deadlines; POST expire persists EXPIRED.
- SMTP delivery is optional via `scripts/send_notifications.py`, outside business transactions.

## Data access

Mọi truy vấn/ghi dữ liệu đều đi qua function trong `src/backend/sql/`, có comment ở đầu. Python service kiểm tra quyền/state machine và điều phối transaction; không đọc/ghi bảng bằng ORM. Chạy `alembic upgrade head` để áp dụng cả schema tuần 6 và migration `d927ac4106b8` cài các store CRUD. Các script admin, seed và email cũng dùng store.

## Endpoints

| Method | Path | Role | Success |
|---|---|---|---|
| GET | /api/companies | public | 200 |
| POST | /api/companies | recruiter | 201 |
| GET | /api/recruiter/company | recruiter | 200 |
| PUT | /api/companies/{company_id} | recruiter | 200 |
| GET | /api/companies/{company_id} | public | 200 |
| GET | /api/companies/{company_id}/members | recruiter | 200 |
| POST | /api/companies/{company_id}/members | recruiter | 201 |
| DELETE | /api/companies/{company_id}/members/{user_id} | recruiter | 204 |
| GET | /api/admin/companies | admin | 200 |
| POST | /api/admin/companies/{company_id}/review | admin | 200 |
| POST | /api/companies/{company_id}/jobs | recruiter | 201 |
| GET | /api/companies/{company_id}/jobs | public | 200 |
| GET | /api/recruiter/companies/{company_id}/jobs | recruiter | 200 |
| GET | /api/admin/jobs/pending | admin | 200 |
| GET | /api/recruiter/jobs/{job_id} | recruiter | 200 |
| PUT | /api/jobs/{job_id} | recruiter | 200 |
| GET | /api/jobs/{job_id} | public | 200 |
| POST | /api/jobs/{job_id}/submit | recruiter | 200 |
| POST | /api/jobs/{job_id}/approve | admin | 200 |
| POST | /api/jobs/{job_id}/reject | admin | 200 |
| POST | /api/jobs/{job_id}/close | recruiter | 200 |
| GET | /api/skills | public | 200 |
| POST | /api/skills | admin | 201 |
| GET | /api/applicants/me/skills | applicant | 200 |
| PUT | /api/applicants/me/skills | applicant | 200 |
| POST | /api/resumes | applicant | 201 |
| GET | /api/resumes | applicant | 200 |
| PUT | /api/resumes/{resume_id}/default | applicant | 200 |
| GET | /api/resumes/{resume_id}/download | applicant | 200 |
| DELETE | /api/resumes/{resume_id} | applicant | 204 |
| POST | /api/applications | applicant | 201 |
| GET | /api/applications/me | applicant | 200 |
| GET | /api/jobs/{job_id}/applications | recruiter | 200 |
| GET | /api/applications/{application_id} | applicant | 200 |
| PUT | /api/applications/{application_id}/note | recruiter | 200 |
| POST | /api/applications/{application_id}/status | recruiter | 200 |
| POST | /api/applications/{application_id}/withdraw | applicant | 200 |
| GET | /api/applications/{application_id}/resume | applicant | 200 |
| POST | /api/applications/{application_id}/interviews | recruiter | 201 |
| GET | /api/applications/{application_id}/interviews | applicant | 200 |
| POST | /api/interviews/{interview_id}/cancel | recruiter | 200 |
| POST | /api/interviews/{interview_id}/result | recruiter | 200 |
| POST | /api/applications/{application_id}/offers | recruiter | 201 |
| GET | /api/applications/{application_id}/offers | applicant | 200 |
| GET | /api/offers/{offer_id} | applicant | 200 |
| POST | /api/offers/{offer_id}/send | recruiter | 200 |
| POST | /api/offers/{offer_id}/accept | applicant | 200 |
| POST | /api/offers/{offer_id}/reject | applicant | 200 |
| POST | /api/offers/{offer_id}/expire | applicant | 200 |
| GET | /api/notifications | applicant | 200 |
| PUT | /api/notifications/{notification_id}/read | applicant | 200 |
| GET | /api/jobs | public | 200 |
| POST | /api/auth/register | public | 201 |
| POST | /api/auth/login | public | 200 |
| POST | /api/auth/refresh | public | 200 |
| POST | /api/auth/logout | public | 204 |
| GET | /api/auth/me | applicant | 200 |
| GET | /api/applicants/me | applicant | 200 |
| PUT | /api/applicants/me | applicant | 200 |
| GET | /api/health | applicant | 200 |

`applicant` on shared application/interview/offer reads means the applicant owner or a recruiter of the associated company; draft offers remain hidden from applicants. Offer expire is available to the owner or company recruiter. Notifications are available to any active authenticated role for its own records. See Swagger DTOs for exact bodies.

## Scope

Implemented source covers the Week 4–6 backend workflows. Recommendations/AI, reporting and broad admin user moderation are Week 7 work. The automated full HTTP/PostgreSQL verification is separate from manual Postman acceptance; importing the collection does not certify the plan complete.
