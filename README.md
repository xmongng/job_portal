# Job Portal Backend

Backend học tập dùng Python 3.12+, FastAPI, PostgreSQL 16, SQLAlchemy và Alembic. Ba vai trò: ADMIN, RECRUITER, APPLICANT. Frontend đã được gỡ; phạm vi hiện tại gồm các API đến tuần 7 và công cụ kiểm thử/bàn giao tuần 8. Xem [đối chiếu plan](docs/verification/PLAN_COMPLETION.md).

## Đọc và viết code

Bắt đầu từ [hướng dẫn đọc code](docs/architecture/BACKEND_GUIDE.md).

- `src/backend/app/api/routes/`: endpoint HTTP và response DTO.
- `src/backend/app/application/<feature>/`: quyền, trạng thái và các bước xử lý nghiệp vụ bằng Python.
- `src/backend/sql/`: toàn bộ store đọc/ghi dữ liệu, có comment trước mỗi function và chia theo chức năng.
- `src/backend/app/infrastructure/persistence/models/`: định nghĩa bảng SQLAlchemy.
- `src/backend/migrations/`: tạo/cập nhật bảng và snapshot function theo phiên bản.

Mọi thao tác dữ liệu đều qua store. Route gọi Python service để kiểm tra quyền/điều kiện; service gọi store trong transaction. Có thể Command-click vào service để đọc luồng nghiệp vụ; tìm tên function trong `sql/` để xem câu SQL. SQLAlchemy chỉ thực thi function và quản lý transaction, không dùng ORM CRUD trong API.

## Cài và chạy local

Từ thư mục repo:

```bash
cd src/backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp ../../.env.example .env
```

Nếu môi trường đã cài, chỉ cần `source dev-env.sh`. Có thể dùng `uv pip install -e '.[dev]'` nếu .venv được tạo bằng uv và chưa có pip.

Trong `.env`, cấu hình `DATABASE_URL` tới PostgreSQL local (hostname `localhost`, đúng tài khoản/mật khẩu/database), `JWT_SECRET` ít nhất 32 ký tự và `FILE_STORAGE_PATH` tới thư mục private có quyền ghi.

```bash
alembic upgrade head
python scripts/create_admin.py --email admin@example.com
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Migration tạo schema và cài các SQL function; không cần chạy từng file SQL thủ công. Database đã chạy revision ban đầu sẽ được nâng cấp, không phải tạo lại. Database hiện có chưa tự nâng cấp chỉ vì bạn pull code.

Swagger: http://127.0.0.1:8000/docs. Health: http://127.0.0.1:8000/api/health.

## Các luồng đã triển khai

- Register/login, refresh-token rotation, logout và JWT gắn session có thể thu hồi.
- Company + OWNER/MEMBER membership; admin duyệt company trước khi đăng job.
- Draft/submit/approve/reject/close job, public search/filter/pagination và history.
- Profile, education/experience, skill catalogue và lựa chọn skills của applicant.
- Upload/list/default/delete/download PDF CV private (tối đa 5 MiB).
- Apply với snapshot CV, xem đơn, note nội bộ, screening/interview, reject/withdraw và history.
- Interview scheduling, kiểm tra trùng lịch, cancel và ghi kết quả.
- Offer draft/send/accept/reject/expire, một offer active/application.
- In-app notifications, đánh dấu đã đọc và email SMTP local tùy chọn qua worker sau commit.

- Recommendation theo quy tắc skills/location/salary; AI giải thích match và draft JD với fallback.
- Admin quản lý trạng thái user/company, audit log, báo cáo aggregate và CSV.

Schema hiện có 14 bảng nghiệp vụ ban đầu cộng 3 bảng history/audit. Các API riêng tư luôn kiểm tra quyền theo user/company; không chỉ kiểm tra role.

## Postman và kiểm chứng

Xem [API contract](docs/api/API.md), [luồng Postman](docs/flows/week6-postman.md) và import `docs/postman/JobPortal.postman_collection.json`. Chọn PDF thật trong request upload và cấu hình credentials/ID tương ứng. Collection phục vụ kiểm tra thủ công theo workflow, không chạy toàn bộ ngẫu nhiên.

Xem thêm [Week 7–8 Postman](docs/flows/final-postman.md), [deployment/backup](docs/deployment/DEPLOYMENT.md). AI mặc định tắt (`AI_PROVIDER=none`); Gemini chỉ bật khi cấu hình API key/model.

Các test sẵn có (test PostgreSQL cần `TEST_DATABASE_URL` tới database riêng `_test`):

```bash
python -m pytest -q
ruff check .
```

Docker Compose hiện chỉ gồm API + PostgreSQL và MailHog tùy chọn, không còn frontend. API container tự áp dụng migration khi khởi động. Chạy từ repo root bằng `docker compose up --build`; dùng port 8000 ở host.

Không commit `.env`, file CV, virtual environment hoặc dữ liệu PostgreSQL. Xem [CONTRIBUTING.md](CONTRIBUTING.md) để biết quy ước commit.
