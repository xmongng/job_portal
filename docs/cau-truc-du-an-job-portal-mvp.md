# CẤU TRÚC DỰ ÁN — JOB PORTAL MVP (5 TUẦN)

> File này đi kèm `phan-tich-bai-toan-job-portal-mvp.md`. Cấu trúc dưới đây đã **rút gọn từ bản kiến trúc gốc**: bỏ các thư mục/module phục vụ hạ tầng nặng (Elasticsearch, message broker, k8s, versioning phức tạp...) không cần cho 5 tuần, đồng thời **bổ sung sẵn phần cấu hình Design System (màu sắc)** ở frontend để áp dụng ngay từ tuần 1.

---

# 1. Cấu trúc repo tổng quan

```text
job-portal/
│
├── README.md
├── .gitignore
├── .editorconfig
├── .env.example
├── docker-compose.yml
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # 1 workflow: build + test cơ bản
│
├── docs/
│   ├── SRS.md                         # yêu cầu, use case, acceptance criteria
│   ├── ERD.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── flows/
│   │   ├── job-approval.md
│   │   └── application-interview-offer.md
│   ├── postman/
│   │   └── JobPortal.postman_collection.json
│   └── templates/
│       └── cv-template.md
│
├── src/
│   ├── backend/                       # xem mục 2
│   └── frontend/                      # xem mục 3
│
└── scripts/
    └── seed-data.sql                  # hoặc seed qua code, xem mục 6
```

**Đã bỏ so với bản gốc:** thư mục riêng cho Elasticsearch config, message broker, k8s manifest, docker-compose.override.yml (gộp thẳng vào 1 file cho gọn), workflow `cd.yml` riêng (gộp vào `ci.yml` nếu cần deploy demo).

---

# 2. Cấu trúc Backend — Python + FastAPI, Clean Architecture nhẹ

```text
src/backend/
├── pyproject.toml
│
├── app/domain/                  # Không phụ thuộc framework/database
│   ├── entities/
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── job.py
│   │   ├── skill.py
│   │   ├── applicant.py
│   │   ├── resume.py
│   │   ├── application.py
│   │   ├── application_status_history.py
│   │   ├── interview.py
│   │   ├── offer.py
│   │   └── notification.py
│   ├── enums/
│   │   ├── job_status.py               # Draft, PendingApproval, Published, Rejected, Closed
│   │   ├── application_status.py       # Applied, Screening, Interview, Offer, Hired, Rejected, Withdrawn
│   │   ├── offer_status.py
│   │   └── user_role.py                # Admin, Recruiter, Applicant
│   └── common/
│       └── auditable_entity.py         # CreatedAt/CreatedBy tối giản
│
├── app/application/              # Use case, DTO, interface
│   ├── auth/
│   │   ├── commands/ (Register, Login, RefreshToken, ForgotPassword, ResetPassword)
│   │   └── dtos/
│   ├── companies/
│   │   ├── commands/ (CreateCompany, UpdateCompany)
│   │   └── queries/ (GetCompanyById, ListCompanies)
│   ├── jobs/
│   │   ├── commands/ (CreateJob, UpdateJob, SubmitJob, ApproveJob, RejectJob, CloseJob)
│   │   └── queries/ (SearchJobs, GetJobById, ListPendingJobs)
│   ├── applicants/
│   │   ├── commands/ (UpdateProfile, UploadResume, DeleteResume, SetDefaultResume)
│   │   └── queries/ (GetProfile, ListResumes)
│   ├── applications/
│   │   ├── commands/ (Apply, ChangeStatus, WithdrawApplication)
│   │   └── queries/ (GetMyApplications, GetApplicationsByJob)
│   ├── interviews/
│   │   ├── commands/ (ScheduleInterview, RecordResult)
│   │   └── queries/ (GetInterviewsByApplication)
│   ├── offers/
│   │   ├── commands/ (CreateOffer, AcceptOffer, RejectOffer)
│   │   └── queries/ (GetOfferByApplication)
│   ├── recommendations/
│   │   └── queries/ (GetRecommendedJobs)         # rule-based scoring, mục 4.1 file phân tích
│   ├── ai/
│   │   ├── assistant.py                         # protocol — dễ tắt/mock khi cần
│   │   ├── explain_match.py                     # mục 4.2
│   │   └── generate_job_description.py          # mục 4.3
│   ├── reports/
│   │   └── queries/ (JobCountReport, ApplicantCountReport)
│   ├── notifications/
│   │   └── service.py
│   └── common/
│       ├── ports/ (FileStorage, CurrentUser, EmailSender, database session)
│       └── validation/ (Pydantic schemas)
│
├── app/infrastructure/            # SQLAlchemy, PostgreSQL, file, email, AI
│   ├── persistence/
│   │   ├── database.py
│   │   ├── models/             # SQLAlchemy model/schema cho từng entity
│   │   └── migrations/
│   ├── file_storage/
│   │   └── local_private_storage.py    # lưu ngoài webroot, random filename
│   ├── email/
│   │   └── smtp_sender.py              # dùng SMTP client, trỏ tới MailHog khi dev
│   ├── ai/
│   │   └── llm_http_assistant.py       # gọi httpx tới OpenAI/Gemini, có fallback
│   ├── reporting/
│   │   └── csv_exporter.py
│   └── dependencies.py
│
├── app/api/                       # FastAPI router, middleware, auth policy
│   ├── routes/
│   │   ├── auth.py
│   │   ├── companies.py
│   │   ├── jobs.py
│   │   ├── applicants.py
│   │   ├── applications.py
│   │   ├── interviews.py
│   │   ├── offers.py
│   │   ├── recommendations.py
│   │   ├── ai.py
│   │   ├── reports.py
│   │   └── notifications.py
│   ├── middleware/
│   │   ├── exception_handler.py
│   │   └── audit.py                     # ghi audit_logs cho action nhạy cảm
│   ├── authorization/
│   │   ├── resource_access.py           # recruiter chỉ thao tác company/job của mình
│   │   └── policies.py
│   └── main.py
│
└── tests/
    ├── unit/
    │   ├── jobs/JobStateMachineTests.py
    │   ├── applications/ApplicationStatusTests.py
    │   └── recommendations/test_scoring.py
    └── integration/
        ├── test_auth_flow.py
        ├── test_job_approval_flow.py
        └── test_apply_flow.py
```

**Đã bỏ/gộp so với bản gốc:** không tạo generic repository cho mọi entity (dùng SQLAlchemy session qua application port), không có thư mục riêng cho background-job queue, và không có module Redis/cache ở giai đoạn đầu.

---

# 3. Cấu trúc Frontend — React + TypeScript + Vite

```text
src/frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
│
├── public/
│   └── favicon.svg
│
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── router.tsx
    │
    ├── styles/
    │   └── globals.css                # import font Inter, biến CSS màu
    │
    ├── theme/
    │   └── tokens.ts                  # export lại token màu dùng trong TS (badge, chart...)
    │
    ├── components/
    │   ├── ui/                        # Button, Input, Card, Badge, Modal, Table, Pagination
    │   │   ├── Button.tsx
    │   │   ├── Badge.tsx              # nhận prop status -> tự map màu theo tokens
    │   │   ├── Card.tsx
    │   │   ├── Table.tsx
    │   │   └── Pagination.tsx
    │   ├── layout/
    │   │   ├── AppShell.tsx           # sidebar + header dùng chung
    │   │   ├── PublicHeader.tsx
    │   │   └── RoleSidebar.tsx        # đổi menu theo role
    │   └── charts/
    │       └── SimpleBarChart.tsx     # Recharts, dùng cho báo cáo/dashboard
    │
    ├── features/
    │   ├── auth/
    │   │   ├── pages/ (LoginPage, RegisterPage, ForgotPasswordPage)
    │   │   └── api/authApi.ts
    │   ├── public/
    │   │   └── pages/ (HomePage, JobListPage, JobDetailPage, CompanyListPage, CompanyDetailPage)
    │   ├── applicant/
    │   │   ├── pages/
    │   │   │   ├── ApplicantDashboardPage.tsx
    │   │   │   ├── ProfilePage.tsx
    │   │   │   ├── ResumesPage.tsx
    │   │   │   ├── ApplicationsPage.tsx
    │   │   │   ├── ApplicationDetailPage.tsx
    │   │   │   ├── InterviewsPage.tsx
    │   │   │   ├── OffersPage.tsx
    │   │   │   ├── RecommendationsPage.tsx    # gợi ý AI + giải thích match
    │   │   │   └── NotificationsPage.tsx
    │   │   └── api/
    │   ├── recruiter/
    │   │   ├── pages/
    │   │   │   ├── RecruiterDashboardPage.tsx  # Kanban pipeline đơn giản
    │   │   │   ├── CompanyPage.tsx
    │   │   │   ├── JobsPage.tsx
    │   │   │   ├── JobEditorPage.tsx           # có nút "Soạn JD bằng AI"
    │   │   │   ├── JobApplicationsPage.tsx
    │   │   │   ├── ApplicationDetailPage.tsx
    │   │   │   ├── InterviewsPage.tsx
    │   │   │   └── OffersPage.tsx
    │   │   └── api/
    │   └── admin/
    │       ├── pages/
    │       │   ├── AdminDashboardPage.tsx
    │       │   ├── PendingJobsPage.tsx
    │       │   ├── CompaniesPage.tsx
    │       │   ├── UsersPage.tsx
    │       │   ├── ReportsPage.tsx
    │       │   └── AuditLogsPage.tsx
    │       └── api/
    │
    ├── hooks/
    │   ├── useAuth.ts
    │   └── useCurrentUser.ts
    │
    └── lib/
        ├── httpClient.ts               # fetch wrapper, tự đính JWT + xử lý refresh token
        └── queryClient.ts              # cấu hình TanStack Query
```

**Danh sách route rút gọn (đủ cho 5 tuần, khớp với danh sách trang ở trên):**

```text
Public:    /  /jobs  /jobs/:id  /companies  /companies/:id  /login  /register  /forgot-password
Applicant: /applicant/dashboard /profile /resumes /applications /applications/:id
           /interviews /offers /recommendations /notifications
Recruiter: /recruiter/dashboard /company /jobs /jobs/new /jobs/:id/edit
           /jobs/:id/applications /applications/:id /interviews /offers
Admin:     /admin/dashboard /admin/jobs/pending /admin/companies /admin/users
           /admin/reports /admin/audit-logs
```

---

# 4. Design System áp vào code (đồng bộ với file phân tích, mục 7)

```css
/* src/frontend/src/styles/globals.css — Tailwind CSS 4 */
@import "tailwindcss";

@theme {
  --font-sans: Inter, system-ui, sans-serif;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-accent: #10b981;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-status-draft-bg: #f1f5f9;
  --color-status-draft-text: #64748b;
  --color-status-pending-bg: #fef3c7;
  --color-status-pending-text: #b45309;
  --color-status-offer-bg: #ccfbf1;
  --color-status-offer-text: #0f766e;
  --color-status-hired-bg: #ecfdf5;
  --color-status-hired-text: #047857;
  --radius-card: 12px;
  --radius-modal: 16px;
  --shadow-card: 0 1px 3px rgb(15 23 42 / 6%);
}
```

```tsx
// src/frontend/src/components/ui/Badge.tsx (ví dụ map trạng thái -> màu)
const statusStyles: Record<string, string> = {
  Draft: 'bg-status-draft-bg text-status-draft-text',
  PendingApproval: 'bg-status-pending-bg text-status-pending-text',
  Offer: 'bg-status-offer-bg text-status-offer-text',
  Hired: 'bg-status-hired-bg text-status-hired-text',
}
```

---

# 5. Docker Compose tối giản

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: jobportal
      POSTGRES_USER: jobportal
      POSTGRES_PASSWORD: jobportal
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  api:
    build: ./src/backend
    env_file: .env
    depends_on: [postgres]
    ports: ["5000:5000"]
    volumes:
      - resumes:/app-data/private/resumes   # CV private, không expose static

  web:
    build: ./src/frontend
    depends_on: [api]
    ports: ["5173:80"]

  # Optional — thêm khi cần test email, không bắt buộc cho demo cốt lõi
  mailhog:
    image: mailhog/mailhog
    ports: ["8025:8025", "1025:1025"]

volumes:
  pgdata:
  resumes:
```

**Đã bỏ:** service `redis` (thêm sau nếu dư thời gian — xem backlog P1 ở file phân tích), `docker-compose.override.yml` riêng (gộp thẳng vào 1 file).

---

# 6. File cấu hình quan trọng khác

```text
.env.example
  DB_CONNECTION_STRING=Host=postgres;Database=jobportal;Username=jobportal;Password=jobportal
  JWT_SECRET=change-me
  JWT_EXPIRES_MINUTES=60
  AI_PROVIDER=openai            # openai | gemini | none (tắt AI hoàn toàn nếu cần)
  AI_API_KEY=
  SMTP_HOST=mailhog
  SMTP_PORT=1025
  FILE_STORAGE_PATH=/app-data/private/resumes
```

- `AI_PROVIDER=none` cho phép **tắt hoàn toàn tính năng AI** trong `AiAssistant` mà không cần sửa code các module khác — quan trọng để đảm bảo phần lõi vẫn chạy được nếu AI gặp sự cố ngay trước demo.
- `scripts/seed-data.sql` (hoặc 1 `SeedDataService` chạy khi start ở môi trường Development): sinh ~200–300 record cho `companies/jobs/applicants/applications` kèm 3 tài khoản demo cố định (`admin@jobportal.local`, `recruiter@techcorp.local`, `applicant@example.local`).

---

# 7. Ghi chú map cấu trúc theo lộ trình 5 tuần

| Tuần | Phần cấu trúc cần hoàn thiện |
|---|---|
| 1 | `JobPortal.Domain`, `Persistence` cơ bản, `AuthController`, `Authorization`, `features/auth`, `features/admin/PendingJobsPage` |
| 2 | `Jobs` (Application), `JobsController` search, `features/public`, `Applicants`, `FileStorage`, `features/applicant/ProfilePage|ResumesPage` |
| 3 | `Applications`, `ApplicationsController`, `features/recruiter/JobApplicationsPage`, `Notifications` |
| 4 | `Interviews`, `Offers`, `Recommendations`, `Ai/*`, `features/applicant/RecommendationsPage`, `features/recruiter/JobEditorPage` (nút AI) |
| 5 | `Reports`, `tests/*`, hoàn thiện `components/ui`, `theme/tokens.ts`, seed data, README demo |
