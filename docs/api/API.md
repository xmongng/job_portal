# API Contract

Base path: `/api`. OpenAPI tương tác tại `/docs` khi chạy FastAPI.

## API đã có

| Method | Path | Ý nghĩa |
|---|---|---|
| GET | `/api/health` | Kiểm tra backend hoạt động |
| GET | `/api/jobs` | Danh sách job công khai còn hạn |
| GET | `/api/jobs/{job_id}` | Chi tiết một job công khai |
| GET | `/api/companies` | Danh sách công ty đã xác minh |
| GET | `/api/companies/{company_id}/jobs` | Job công khai của một công ty |

Hai API job gọi stored functions `public.list_public_jobs()` và `public.get_public_job(uuid)`. ID truyền vào câu SQL bằng bind parameter.

## API sẽ triển khai theo thứ tự

| Giai đoạn | Prefix | Nghiệp vụ |
|---|---|---|
| 1 | `/api/auth` | Register, login, refresh, logout |
| 2 | `/api/companies`, `/api/jobs` | CRUD và authorization theo membership |
| 3 | `/api/applicants`, `/api/resumes` | Hồ sơ, skills và CV |
| 4 | `/api/applications` | Apply, xem và cập nhật trạng thái |
| 5 | `/api/interviews`, `/api/offers` | Phỏng vấn và offer |
| 6 | `/api/notifications` | Danh sách và đánh dấu đã đọc |
| 7 | `/api/recommendations`, `/api/ai` | Matching rule-based, giải thích match và soạn JD |

API private phải kiểm tra role và quyền trên resource; không nhận `user_id` hoặc `company_id` đặc quyền từ client nếu có thể suy ra từ phiên đăng nhập.
