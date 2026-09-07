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

# 2. Cấu trúc Backend — Node.js + Express + TypeScript, Clean Architecture nhẹ

```text
src/backend/
├── package.json
│
├── src/domain/                  # Không phụ thuộc framework/database
│   ├── Entities/
│   │   ├── User.ts
│   │   ├── Company.ts
│   │   ├── Job.ts
│   │   ├── Skill.ts
│   │   ├── Applicant.ts
│   │   ├── Resume.ts
│   │   ├── Application.ts
│   │   ├── ApplicationStatusHistory.ts
│   │   ├── Interview.ts
│   │   ├── Offer.ts
│   │   └── Notification.ts
│   ├── Enums/
│   │   ├── JobStatus.ts               # Draft, PendingApproval, Published, Rejected, Closed
│   │   ├── ApplicationStatus.ts       # Applied, Screening, Interview, Offer, Hired, Rejected, Withdrawn
│   │   ├── OfferStatus.ts
│   │   └── UserRole.ts                # Admin, Recruiter, Applicant
│   └── Common/
│       └── AuditableEntity.ts         # CreatedAt/CreatedBy tối giản (không versioning phức tạp)
│
├── src/application/              # Use case, DTO, interface
│   ├── Auth/
│   │   ├── Commands/ (Register, Login, RefreshToken, ForgotPassword, ResetPassword)
│   │   └── Dtos/
│   ├── Companies/
│   │   ├── Commands/ (CreateCompany, UpdateCompany)
│   │   └── Queries/ (GetCompanyById, ListCompanies)
│   ├── Jobs/
│   │   ├── Commands/ (CreateJob, UpdateJob, SubmitJob, ApproveJob, RejectJob, CloseJob)
│   │   └── Queries/ (SearchJobs, GetJobById, ListPendingJobs)
│   ├── Applicants/
│   │   ├── Commands/ (UpdateProfile, UploadResume, DeleteResume, SetDefaultResume)
│   │   └── Queries/ (GetProfile, ListResumes)
│   ├── Applications/
│   │   ├── Commands/ (Apply, ChangeStatus, WithdrawApplication)
│   │   └── Queries/ (GetMyApplications, GetApplicationsByJob)
│   ├── Interviews/
│   │   ├── Commands/ (ScheduleInterview, RecordResult)
│   │   └── Queries/ (GetInterviewsByApplication)
│   ├── Offers/
│   │   ├── Commands/ (CreateOffer, AcceptOffer, RejectOffer)
│   │   └── Queries/ (GetOfferByApplication)
│   ├── Recommendations/
│   │   └── Queries/ (GetRecommendedJobs)         # rule-based scoring, mục 4.1 file phân tích
│   ├── Ai/
│   │   ├── AiAssistant.ts                        # interface — dễ tắt/mock khi cần
│   │   ├── ExplainMatchQuery.ts                    # mục 4.2
│   │   └── GenerateJobDescriptionCommand.ts        # mục 4.3
│   ├── Reports/
│   │   └── Queries/ (JobCountReport, ApplicantCountReport)
│   ├── Notifications/
│   │   └── NotificationService.ts
│   └── Common/
│       ├── Interfaces/ (FileStorage, CurrentUser, EmailSender, AppDbContext)
│       └── Behaviors/ (ValidationHelper — không bắt buộc dùng FluentValidation/MediatR)
│
├── src/infrastructure/            # Drizzle ORM, PostgreSQL, file, email, AI
│   ├── Persistence/
│   │   ├── AppDbContext.ts
│   │   ├── Configurations/             # Drizzle schema cho từng entity
│   │   └── Migrations/
│   ├── FileStorage/
│   │   └── LocalPrivateFileStorage.ts  # lưu ngoài webroot, random filename
│   ├── Email/
│   │   └── SmtpEmailSender.ts          # dùng Nodemailer, trỏ tới MailHog khi dev
│   ├── Ai/
│   │   └── LlmHttpAiAssistant.ts       # gọi fetch tới OpenAI/Gemini, có fallback
│   ├── Reporting/
│   │   └── CsvReportExporter.ts
│   └── DependencyInjection.ts
│
├── src/api/                       # Router, middleware, auth policy
│   ├── routes/
│   │   ├── AuthRouter.ts
│   │   ├── CompaniesRouter.ts
│   │   ├── JobsRouter.ts
│   │   ├── ApplicantsRouter.ts
│   │   ├── ApplicationsRouter.ts
│   │   ├── InterviewsRouter.ts
│   │   ├── OffersRouter.ts
│   │   ├── RecommendationsRouter.ts
│   │   ├── AiRouter.ts
│   │   ├── ReportsRouter.ts
│   │   └── NotificationsRouter.ts
│   ├── Middleware/
│   │   ├── ExceptionHandlingMiddleware.ts
│   │   └── AuditActionFilter.ts         # ghi audit_logs cho action nhạy cảm (duyệt job, tải CV)
│   ├── Authorization/
│   │   ├── ResourceAuthorizationHandlers.ts  # recruiter chỉ thao tác company/job của mình
│   │   └── Policies.ts
│   ├── server.ts
│   ├── app.ts
│   └── server.ts
│
└── tests/
    ├── unit/
    │   ├── Jobs/JobStateMachineTests.ts
    │   ├── Applications/ApplicationStatusTests.ts
    │   └── Recommendations/ScoringTests.ts
    └── integration/
        ├── AuthFlowTests.ts
        ├── JobApprovalFlowTests.ts
        └── ApplyFlowTests.ts
```

**Đã bỏ/gộp so với bản gốc:** không tạo `IRepository<T>` generic cho mọi entity (dùng thẳng `AppDbContext`), không có thư mục riêng cho background job queue (gửi email/notification xử lý ngay trong use case hoặc qua 1 `worker in-process` đơn giản nếu cần), không có module Redis/cache riêng ở giai đoạn đầu.

---

# 3. Cấu trúc Frontend — React + TypeScript + Vite

```text
src/frontend/
├── index.html
├── vite.config.ts
├── tailwind.config.ts                 # chứa toàn bộ token màu — xem mục 4
├── postcss.config.js
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

```ts
// src/frontend/tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: { DEFAULT: '#2563EB', hover: '#1D4ED8', 50: '#EFF6FF' },
        accent:  { DEFAULT: '#10B981', 50: '#ECFDF5' },
        bg: '#F8FAFC',
        surface: '#FFFFFF',
        border: '#E2E8F0',
        text: { DEFAULT: '#0F172A', muted: '#64748B' },
        status: {
          draftBg: '#F1F5F9',     draftText: '#64748B',
          pendingBg: '#FEF3C7',   pendingText: '#B45309',
          publishedBg: '#EFF6FF',publishedText: '#1D4ED8',
          rejectedBg: '#FEE2E2', rejectedText: '#B91C1C',
          interviewBg: '#EDE9FE',interviewText: '#6D28D9',
          offerBg: '#CCFBF1',    offerText: '#0F766E',
          hiredBg: '#ECFDF5',    hiredText: '#047857',
        },
      },
      borderRadius: { DEFAULT: '8px', card: '12px', modal: '16px' },
      boxShadow: { card: '0 1px 3px rgba(15,23,42,0.06)' },
    },
  },
} satisfies Config
```

```tsx
// src/frontend/src/components/ui/Badge.tsx (ví dụ map trạng thái -> màu)
const statusStyles: Record<string, string> = {
  Draft: 'bg-status-draftBg text-status-draftText',
  PendingApproval: 'bg-status-pendingBg text-status-pendingText',
  Published: 'bg-status-publishedBg text-status-publishedText',
  Rejected: 'bg-status-rejectedBg text-status-rejectedText',
  Applied: 'bg-status-publishedBg text-status-publishedText',
  Screening: 'bg-status-pendingBg text-status-pendingText',
  Interview: 'bg-status-interviewBg text-status-interviewText',
  Offer: 'bg-status-offerBg text-status-offerText',
  Hired: 'bg-status-hiredBg text-status-hiredText',
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
    ports: ["5000:8080"]
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
