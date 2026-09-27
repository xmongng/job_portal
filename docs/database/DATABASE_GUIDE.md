# Hướng dẫn tương tác với cơ sở dữ liệu

Tài liệu này hướng dẫn thao tác PostgreSQL bằng terminal cho dự án Job Portal. Môi trường hiện tại sử dụng PostgreSQL 16 chạy trên máy tại `localhost:5432`.

## 1. Các câu lệnh khởi tạo và ý nghĩa

### 1.1. Mở PostgreSQL bằng database quản trị

```bash
psql -h localhost -d postgres
```

- `psql`: mở chương trình dòng lệnh của PostgreSQL.
- `-h localhost`: kết nối tới PostgreSQL đang chạy trên máy hiện tại.
- `-d postgres`: mở database quản trị mặc định có tên `postgres`.
- Nếu không truyền `-U`, PostgreSQL mặc định thử dùng tên người dùng hiện tại của hệ điều hành.

### 1.2. Tạo tài khoản PostgreSQL cho ứng dụng

```sql
CREATE ROLE jobportal WITH LOGIN PASSWORD 'mong1234';
```

- `CREATE ROLE jobportal`: tạo role có tên `jobportal`.
- `WITH LOGIN`: cho phép role này đăng nhập vào PostgreSQL.
- `PASSWORD`: đặt mật khẩu dùng khi xác thực.
- Dấu `;` kết thúc câu SQL. Nếu thiếu dấu này, `psql` sẽ tiếp tục chờ phần còn lại của câu lệnh.

Mật khẩu trên chỉ phù hợp cho môi trường phát triển local. Không sử dụng mật khẩu yếu hoặc đưa mật khẩu thật lên Git trong môi trường production.

### 1.3. Tạo database và chỉ định chủ sở hữu

```sql
CREATE DATABASE jobportal OWNER jobportal;
```

- `CREATE DATABASE jobportal`: tạo database tên `jobportal`.
- `OWNER jobportal`: gán role `jobportal` làm chủ sở hữu database.
- Chủ sở hữu có quyền tạo, sửa và xóa các đối tượng thuộc database theo quyền PostgreSQL.

### 1.4. Kiểm tra role

```sql
\du jobportal
```

- `\du`: liệt kê role PostgreSQL.
- `jobportal`: giới hạn kết quả theo tên role cần kiểm tra.
- Đây là lệnh riêng của `psql`, không phải câu SQL, nên không cần dấu `;`.

### 1.5. Kiểm tra database

```sql
\l jobportal
```

- `\l`: liệt kê database.
- `jobportal`: lọc database theo tên.
- Kết quả cho biết owner, encoding, locale và quyền truy cập.

### 1.6. Sửa tên database bị nhập sai

Trong quá trình khởi tạo, database từng được nhập nhầm thành `jobprotal`. Lệnh sau đổi nó về tên đúng:

```sql
ALTER DATABASE jobprotal RENAME TO jobportal;
```

- `ALTER DATABASE jobprotal`: chọn database đang có tên sai.
- `RENAME TO jobportal`: đổi sang tên chính xác.

### 1.7. Thoát khỏi PostgreSQL

```sql
\q
```

`\q` đóng phiên `psql` và quay lại terminal thông thường.

### 1.8. Đăng nhập bằng tài khoản của ứng dụng

```bash
psql -h localhost -U jobportal -d jobportal
```

- `-h localhost`: kết nối tới PostgreSQL trên máy.
- `-U jobportal`: đăng nhập bằng role `jobportal`.
- `-d jobportal`: mở database `jobportal`.

Chỉ nhập mật khẩu khi terminal hiển thị thông báo tương tự:

```text
Password for user jobportal:
```

Khi đã thấy dấu nhắc `jobportal=>`, phiên kết nối đã thành công và mọi nội dung nhập tiếp theo được hiểu là SQL hoặc lệnh `psql`, không phải mật khẩu.

### 1.9. Kiểm tra phiên kết nối hiện tại

```sql
SELECT current_database(), current_user;
```

- `current_database()`: trả về database đang mở.
- `current_user`: trả về role đang thực thi câu lệnh.

Kết quả mong đợi:

```text
 current_database | current_user
------------------+-------------
 jobportal        | jobportal
```

### 1.10. Liệt kê các bảng

```sql
\dt
```

`\dt` liệt kê bảng trong schema hiện tại. Database mới chưa chạy migration sẽ hiển thị `Did not find any relations.`

## 2. Ý nghĩa dấu nhắc của `psql`

| Dấu nhắc | Ý nghĩa |
|---|---|
| `postgres=#` | Đang kết nối database `postgres`, thường bằng role có quyền quản trị. |
| `jobportal=>` | Đang kết nối database `jobportal` bằng role thông thường. |
| `jobportal->` | Câu SQL chưa hoàn chỉnh; thường do thiếu dấu `;`, dấu nháy hoặc dấu ngoặc đóng. |

Nếu nhập sai và thấy dấu nhắc `->`, có thể hủy câu lệnh đang soạn bằng:

```text
Ctrl+C
```

## 3. Các thao tác kiểm tra thường dùng

Kết nối vào database ứng dụng:

```bash
psql -h localhost -U jobportal -d jobportal
```

Các lệnh hữu ích bên trong `psql`:

```sql
\conninfo
\dn
\dt
\d users
\x
\q
```

| Lệnh | Công dụng |
|---|---|
| `\conninfo` | Hiển thị thông tin kết nối hiện tại. |
| `\dn` | Liệt kê schema. |
| `\dt` | Liệt kê bảng. |
| `\d users` | Xem cấu trúc bảng `users` sau khi bảng được tạo. |
| `\x` | Bật/tắt chế độ hiển thị mở rộng cho bản ghi có nhiều cột. |
| `\q` | Thoát `psql`. |

Thực thi một câu SQL trực tiếp từ terminal mà không mở phiên tương tác:

```bash
psql -h localhost -U jobportal -d jobportal \
  -c "SELECT current_database(), current_user;"
```

Chạy một file SQL:

```bash
psql -h localhost -U jobportal -d jobportal \
  -f duong/dan/toi/file.sql
```

Thay `duong/dan/toi/file.sql` bằng đường dẫn tới file SQL **đã tồn tại**. Lệnh này thực thi nội dung file trên database đang kết nối; nên đọc file trước khi chạy.

### 3.1. Xem và chọn từng bảng để thao tác

Sau khi đăng nhập và thấy `jobportal=>`, chạy các lệnh sau **trong `psql`**:

```sql
\conninfo
\dt public.*
\d+ public.skills
SELECT id, name, normalized_name, is_active FROM public.skills LIMIT 10;
```

- `\conninfo`: xác nhận đang kết nối đúng database và role trước khi sửa dữ liệu.
- `\dt public.*`: liệt kê các bảng trong schema `public`. `alembic_version` là bảng Alembic dùng theo dõi migration, không phải bảng nghiệp vụ.
- `\d+ public.skills`: xem cột, kiểu dữ liệu, khóa, index và ràng buộc của bảng `skills`.
- `SELECT ... FROM public.skills`: đọc dữ liệu bảng đó; `LIMIT 10` chỉ lấy tối đa 10 dòng. Nếu không có kết quả thì bảng đang rỗng.

Muốn xem bảng khác, thay `skills` bằng tên bảng trong kết quả `\dt public.*`. Ví dụ `\d+ public.jobs` rồi `SELECT * FROM public.jobs LIMIT 10;`. Có thể xem tên cột trước bằng `\d+` để chọn đúng cột trong câu `SELECT`. `psql` không có lệnh “mở bảng” như giao diện SQL Server: `\d` xem cấu trúc, còn `SELECT` xem các dòng dữ liệu.

### 3.2. Ví dụ thêm, sửa và xóa một dòng trong `skills`

Chỉ thử trên database phát triển. Bảng `skills` có `id` kiểu UUID; khi thêm bằng SQL trực tiếp, hãy **cấp `id` rõ ràng** vì giá trị mặc định `uuid4` của model được Python/SQLAlchemy tạo khi ứng dụng ghi dữ liệu, không phải mặc định tại PostgreSQL.

```sql
INSERT INTO public.skills (id, name, normalized_name)
VALUES ('d42d9b0e-5935-4f54-8a5c-8d15335fa93a', 'Python demo', 'python-demo');

SELECT id, name, normalized_name
FROM public.skills
WHERE id = 'd42d9b0e-5935-4f54-8a5c-8d15335fa93a';

UPDATE public.skills
SET name = 'Python demo (updated)', updated_at = now()
WHERE id = 'd42d9b0e-5935-4f54-8a5c-8d15335fa93a';

DELETE FROM public.skills
WHERE id = 'd42d9b0e-5935-4f54-8a5c-8d15335fa93a';
```

Các câu SQL kết thúc bằng `;`. `WHERE id = ...` giới hạn `UPDATE`/`DELETE` vào đúng một dòng; **không bỏ `WHERE`** nếu không muốn tác động cả bảng. Nếu `normalized_name` hoặc `id` đã tồn tại, `INSERT` sẽ bị chặn bởi ràng buộc unique/PK. Nếu một bảng khác đã tham chiếu kỹ năng này, `DELETE` có thể bị FK chặn; không xóa dữ liệu thật chỉ để thử lệnh.

Để thử thay đổi mà không lưu, có thể bọc các lệnh sửa dữ liệu trong transaction:

```sql
BEGIN;
-- Chạy INSERT hoặc UPDATE thử, rồi SELECT để kiểm tra.
ROLLBACK;
```

`ROLLBACK` hủy các thay đổi kể từ `BEGIN`; chỉ dùng `COMMIT;` khi thực sự muốn lưu. Với dữ liệu do backend quản lý, ưu tiên thao tác qua API/SQLAlchemy để các quy tắc nghiệp vụ và lịch sử liên quan được xử lý đúng.

## 4. Kết nối từ backend FastAPI

Khi backend chạy trực tiếp trên máy, URL kết nối sử dụng `localhost`:

```env
DATABASE_URL=postgresql+psycopg://jobportal:mong1234@localhost:5432/jobportal
```

Đặt biến này trong file:

```text
src/backend/.env
```

Không commit file `.env` lên Git. File `.env.example` chỉ nên chứa giá trị mẫu, không chứa mật khẩu thật.

Khi backend chạy trong Docker Compose, hostname phải là tên service `postgres` thay vì `localhost`:

```env
DATABASE_URL=postgresql+psycopg://jobportal:change-me@postgres:5432/jobportal
```

## 5. Tạo và cập nhật bảng

Dự án nên quản lý schema bằng SQLAlchemy và Alembic thay vì tạo bảng thủ công trong `psql`.

Alembic đã được cấu hình và các migration hiện có nằm trong `src/backend/migrations/versions/`. Khi **thay đổi định nghĩa model**, chạy từ thư mục backend:

```bash
cd /Users/mong/Documents/ComputerScience/AI4SE/job_portal/src/backend
source .venv/bin/activate
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

- `revision --autogenerate`: so sánh SQLAlchemy metadata với database và tạo migration nháp.
- Phải đọc lại migration được sinh trước khi chạy.
- `upgrade head`: áp dụng tất cả migration chưa chạy.

Nếu chỉ cần đưa một database mới lên schema hiện tại, **không tạo revision mới**: chỉ chạy `alembic upgrade head`. Kiểm tra phiên bản đang áp dụng bằng `alembic current` hoặc `SELECT * FROM alembic_version;` trong `psql`.

### 5.1. Dữ liệu mẫu để luyện truy vấn

Script `src/backend/scripts/seed_demo.py` tạo 5 bản ghi liên kết hợp lệ cho **mỗi bảng nghiệp vụ**, riêng `users` tạo 11 tài khoản (5 applicant, 5 recruiter, 1 admin) để đúng vai trò và quan hệ với các bảng khác. Không thêm bản ghi vào `alembic_version` vì đây là bảng quản lý migration. Chạy từ thư mục backend khi database mới đã ở migration hiện tại và **tất cả bảng nghiệp vụ còn rỗng**:

```bash
cd /Users/mong/Documents/ComputerScience/AI4SE/job_portal/src/backend
.venv/bin/python scripts/seed_demo.py
```

Script từ chối chạy nếu sai database, sai migration hoặc bất kỳ bảng nghiệp vụ nào đã có dữ liệu. Toàn bộ thao tác dùng một transaction nên lỗi ở giữa sẽ rollback, không tạo bộ dữ liệu dở dang. Database local hiện đã được seed; **không cần chạy lại** trừ khi bạn tạo một database phát triển mới hoàn toàn rỗng.

Thử xem dữ liệu bằng `psql`:

```sql
SELECT id, name, normalized_name FROM public.skills;
SELECT id, title, status FROM public.jobs;
SELECT id, contact_name, status FROM public.applications;
```

Tất cả email có đuôi `.invalid` và mật khẩu bị vô hiệu hóa: các tài khoản này **không đăng nhập được**. Token/phiên đã hết hạn, email và kết quả AI chỉ là bản ghi giả; script không gửi email hay gọi AI. `resumes.storage_key` trỏ đến file placeholder **không tồn tại**, vì vậy không dùng các bản ghi này để thử tải CV. Dữ liệu này chỉ dành cho phát triển và luyện truy vấn, không dùng trong production.

## 6. Sao lưu và khôi phục

Sao lưu database:

```bash
pg_dump -h localhost -U jobportal -d jobportal > jobportal_backup.sql
```

Khôi phục bản sao lưu dạng SQL:

```bash
psql -h localhost -U jobportal -d jobportal < jobportal_backup.sql
```

Không commit file backup chứa dữ liệu người dùng, CV hoặc thông tin nhạy cảm lên Git.

## 7. Nguyên tắc an toàn

- Không nối trực tiếp input của người dùng vào chuỗi SQL.
- Sử dụng SQLAlchemy expression hoặc parameter của Psycopg.
- Backend kết nối bằng role `jobportal`, không dùng role quản trị hệ thống.
- Không ghi mật khẩu database vào source code, log hoặc Git.
- Production phải dùng mật khẩu mạnh và TLS nếu database nằm trên máy khác.
- Thay đổi schema bằng migration có kiểm soát và luôn đọc lại migration tự sinh.
- Sao lưu trước các migration có khả năng mất hoặc biến đổi dữ liệu.
