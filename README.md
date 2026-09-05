# Job Portal MVP

Scaffold kiến trúc cho hệ thống tuyển dụng 3 vai trò: Admin, Recruiter và Applicant.

> Trạng thái hiện tại: **architecture scaffold only**. Repository mới chứa cấu trúc thư mục, file khung và tài liệu; chưa có source code nghiệp vụ.

## Tech stack dự kiến

- Backend: ASP.NET Core 8, Clean Architecture nhẹ
- Database: PostgreSQL 16, Entity Framework Core
- Frontend: React, TypeScript, Vite, Tailwind CSS
- Testing: xUnit, React Testing Library
- Local environment: Docker Compose

## Cấu trúc chính

```text
src/backend/   Domain, Application, Infrastructure, API, tests
src/frontend/  UI components, layouts, features theo role, hooks, shared libraries
docs/          SRS, ERD, API, deployment, flows, Postman và templates
scripts/       Seed/migration/helper scripts
```

Xem [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) để hiểu ownership và quy tắc phụ thuộc.

## Quy ước phát triển

1. Domain không phụ thuộc framework hoặc database.
2. Application chỉ phụ thuộc Domain.
3. Infrastructure hiện thực interface từ Application.
4. API là composition root và không chứa business rule.
5. Frontend tổ chức theo feature/role; component dùng chung đặt tại `components/ui`.
6. Mỗi use case nằm trong một file Command/Query riêng và có test tương ứng.

## Tài khoản demo dự kiến

| Role | Email |
|---|---|
| Admin | `admin@jobportal.local` |
| Recruiter | `recruiter@techcorp.local` |
| Applicant | `applicant@example.local` |

Thông tin triển khai sẽ được bổ sung khi bắt đầu coding.
