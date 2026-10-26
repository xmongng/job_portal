# Chạy và bàn giao Job Portal backend

## Local

Python 3.12+; PostgreSQL 16. File `.env` private ở `src/backend/.env` chứa DATABASE_URL và JWT_SECRET (ít nhất 32 ký tự).

```bash
cd src/backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
alembic upgrade head
python scripts/create_admin.py --email admin@example.com
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Không cần tạo lại venv nếu đã hoạt động. Nếu `python` báo file không tồn tại, kiểm tra symlink `.venv/bin/python`; môi trường ảo từ máy khác không portable, cần tạo lại bằng Python có trên máy đó. Local PostgreSQL/psql đã cài trong `.postgresql/` có thể thêm PATH bằng `source dev-env.sh`.

`FILE_STORAGE_PATH` phải là thư mục private có quyền ghi và backup; không mount static. Đường dẫn tương đối tính theo cwd của process; production dùng đường dẫn tuyệt đối. CV metadata được backup trong DB, file CV/snapshot cần backup volume riêng cùng thời điểm.

## Kiểm chứng tự động riêng biệt

```bash
export TEST_DATABASE_URL='postgresql+psycopg://user:password@localhost/jobportal_test'
pytest -q
ruff check .
alembic check
```

Test tích hợp chỉ chấp nhận tên database `_test`, tự chạy migration và rollback dữ liệu. Không trỏ biến test vào database phát triển/production. Test concurrency tạo dữ liệu commit ngắn trong database test và tự cleanup; không chạy hai suite trên cùng một database test.

CI có PostgreSQL service và chạy cả migration lẫn test tích hợp. Database migration dùng frozen SQL; khi sửa store đã triển khai cần migration mới.

## Docker local

```bash
docker compose up --build -d
```

API host port 8000; PostgreSQL port 5432. API đợi healthcheck DB và áp dụng migration trước khi phục vụ. MailHog chỉ bật với `--profile email`. Docker engine phải đang chạy. Không có frontend.

## Production

Chuẩn bị `.env.production` private dựa trên `.env.example`, mật khẩu DB mạnh, JWT_SECRET riêng và host/domain chính xác. DATABASE_URL trong container dùng hostname `postgres`. Không dùng secret mẫu. Ví dụ cấu hình bổ sung:

```env
ALLOWED_HOSTS=["api.example.com","localhost","127.0.0.1"]
CORS_ORIGINS=["https://your-frontend.example.com"]
AI_PROVIDER=none
SMTP_ENABLED=false
```

```bash
ENV_FILE=.env.production docker compose -f docker-compose.prod.yml up --build -d
```

Compose production không expose PostgreSQL và bind API vào loopback `127.0.0.1:8000`. Đặt reverse proxy Nginx/Caddy terminate HTTPS trước API; chuyển Host đúng ALLOWED_HOSTS và không public đường dẫn CV. Default server không tin proxy headers. Nếu cần IP thật để rate-limit, cấu hình ASGI trusted proxies chỉ cho địa chỉ proxy cụ thể; không tin X-Forwarded-For từ Internet.

CORS mặc định không có origin được cho phép; Postman/server clients không cần CORS. Credentials/token không log; request log chỉ ghi request ID, method, route template và status. Rate limiter là basic per-process; cần shared store nếu triển khai nhiều workers/instances.

Docker build/runtime và live HTTPS/SMTP/AI cần xác minh trên hạ tầng đích; việc có file cấu hình không thay cho deploy thật. AI tắt vẫn có fallback đầy đủ. Email worker chạy định kỳ riêng sau commit, xem `docs/flows/week6-postman.md`.

## Backup/restore không ghi đè

Từ backend, dùng `PGHOST/PGPORT/PGUSER/PGDATABASE` và password prompt hoặc `.pgpass` (không đưa mật khẩu vào command):

```bash
sh scripts/backup_database.sh /private/backups/jobportal.dump
sh scripts/restore_database.sh /private/backups/jobportal.dump jobportal_restore
```

Backup từ chối ghi đè file. Restore chỉ tạo database mới hậu tố `_restore`, thất bại nếu database đã tồn tại; không xóa database nào. Sau restore kiểm tra `alembic current`, số bảng, login/role và file storage trước khi chuyển traffic. Backup DB không bao gồm volume CV; sao lưu cả hai. Không commit backup hoặc CV lên Git.
