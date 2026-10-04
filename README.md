# Job Portal MVP

Scaffold kiến trúc cho hệ thống tuyển dụng 3 vai trò: Admin, Recruiter và Applicant.

> Trạng thái hiện tại: **schema 14 bảng đã có và 3 API company công khai đã được viết**. Backend giữ model, migration tạo bảng, kết nối database và cấu hình; API jobs đã được reset. Frontend đã được gỡ khỏi source để tập trung backend. Viết API tại `src/backend/app/api/routes/` và store company tại `src/backend/sql/company.sql`.

## Tech stack dự kiến

- Backend: Python 3.12+, FastAPI, kiến trúc phân lớp nhẹ
- Database: PostgreSQL 16, SQLAlchemy và Psycopg
- Frontend: React 19, TypeScript, Vite, Tailwind CSS
- Testing: Vitest, React Testing Library
- Local environment: Docker Compose

## Cấu trúc chính

```text
src/backend/   Domain, Application, Infrastructure, API, tests
src/frontend/  UI components, layouts, features theo role, hooks, shared libraries
docs/          SRS, ERD, API, deployment, flows, Postman và templates
scripts/       Seed/migration/helper scripts
```

Xem [PROJECT_STRUCTURE.md](docs/architecture/PROJECT_STRUCTURE.md) để hiểu ownership và quy tắc phụ thuộc.

## Chạy scaffold

Backend:

```bash
cd src/backend
cp ../../.env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 5000
```

Frontend (terminal khác):

```bash
cd src/frontend
npm ci
npm run dev
```

API health check: `http://localhost:5000/api/health`. FastAPI documentation: `http://localhost:5000/docs`. Frontend: `http://localhost:5173`.

Trước khi chạy backend trực tiếp ngoài Docker, đổi hostname `postgres` trong `src/backend/.env` thành `localhost`.

Sau khi tạo database PostgreSQL và cấu hình `DATABASE_URL`, tạo/cập nhật bảng bằng:

```bash
cd src/backend
source .venv/bin/activate
alembic upgrade head
```

Schema hiện được quản lý qua `app/infrastructure/persistence/models/` và `migrations/versions/`. Các quy tắc liên quan quyền, trạng thái, file CV và transaction cần được thực hiện trong use case/API; chỉ có model và bảng chưa tạo ra chức năng nghiệp vụ.

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
