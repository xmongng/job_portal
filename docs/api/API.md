# API Contract

Base path: `/api`. OpenAPI tương tác tại `/docs` khi chạy FastAPI.

## API hiện có

| Method | Path | Ý nghĩa |
|---|---|---|
| GET | `/api/health` | Kiểm tra backend hoạt động |
| GET | `/api/companies` | Danh sách công ty đã xác minh và đang hoạt động |
| GET | `/api/companies/{company_id}` | Chi tiết công ty công khai |
| GET | `/api/companies/{company_id}/jobs` | Job đã đăng và còn hạn của công ty |

API company gọi stored functions trong `src/backend/sql/company.sql`; các UUID được truyền bằng bind parameter. Company không tồn tại/không công khai trả 404; UUID sai định dạng trả 422; danh sách rỗng trả 200 với `[]`.

Sau `alembic upgrade head`, cài các function bằng `psql -h localhost -U jobportal -d jobportal -v ON_ERROR_STOP=1 -f sql/company.sql` từ thư mục backend. Hiện các function company được cài thủ công, chưa có migration riêng.

Chạy FastAPI ở port 8000 để tránh xung đột AirTunes trên macOS. API jobs đã được reset để tự triển khai sau.

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
