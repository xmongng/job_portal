# Project Structure

## Dependency direction

```text
JobPortal.Api ───────────────┐
                            ▼
JobPortal.Infrastructure → JobPortal.Application → JobPortal.Domain
```

- `Domain`: entity, enum, domain rule/state machine; không import EF Core/ASP.NET.
- `Application`: use case, DTO, validation và abstraction cho external service.
- `Infrastructure`: persistence, file storage, email, AI provider và reporting.
- `Api`: HTTP contract, authentication/authorization, middleware và DI composition.

## Backend conventions

- Một file cho mỗi public type.
- Command thay đổi state; Query chỉ đọc dữ liệu.
- Feature folder dùng tên số nhiều (`Jobs`, `Applications`).
- Interface hạ tầng đặt trong `Application/Common/Interfaces`.
- EF configuration tách khỏi entity và đặt trong `Persistence/Configurations`.
- Migration chỉ được tạo từ project Infrastructure.
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
| C# type/file | PascalCase | `ApproveJobCommand.cs` |
| React component | PascalCase | `JobListPage.tsx` |
| Hook | camelCase, prefix `use` | `useCurrentUser.ts` |
| API module | camelCase + `Api` | `jobsApi.ts` |
| Route | kebab-case | `/forgot-password` |
| Database | snake_case | `application_status_history` |
