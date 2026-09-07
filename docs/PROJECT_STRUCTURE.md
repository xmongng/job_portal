# Project Structure

## Dependency direction

```text
API ───────────────┐
                  ▼
Infrastructure → Application → Domain
```

- `Domain`: entity, enum, domain rule/state machine; không import FastAPI/SQLAlchemy.
- `Application`: use case, DTO, validation và abstraction cho external service.
- `Infrastructure`: persistence, file storage, email, AI provider và reporting.
- `API`: FastAPI routers, HTTP contract, authentication/authorization, middleware và dependency composition.

## Backend conventions

- Một module Python cho mỗi use case hoặc domain concept.
- Command thay đổi state; Query chỉ đọc dữ liệu.
- Feature folder dùng tên số nhiều (`Jobs`, `Applications`).
- Port/interface hạ tầng đặt trong `application/ports`.
- PostgreSQL schema và repository đặt trong `infrastructure/persistence`.
- Migration chỉ được tạo và chạy từ infrastructure.
- Unit test phản chiếu đường dẫn source; integration test đặt theo business flow.

## Frontend conventions

- `features/<area>/pages`: route-level component.
- `features/<area>/api`: query/mutation và DTO của feature.
- `components/ui`: primitive không biết business domain.
- `components/layout`: shell/header/sidebar dùng chung.
- `lib`: HTTP/query client; `hooks`: cross-feature hooks.
- Không gọi `fetch` trực tiếp trong page; dùng API module của feature.
- Màu, badge và chart phải đọc từ design tokens.

## Naming

| Artifact | Convention | Example |
|---|---|---|
| Python use case | snake_case | `approve_job.py` |
| React component | PascalCase | `JobListPage.tsx` |
| Hook | camelCase, prefix `use` | `useCurrentUser.ts` |
| API module | camelCase + `Api` | `jobsApi.ts` |
| Route | kebab-case | `/forgot-password` |
| Database | snake_case | `application_status_history` |
