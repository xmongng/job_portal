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
  -f scripts/seed-data.sql
```

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

Quy trình dự kiến:

```bash
cd /Users/mong/Documents/ComputerScience/AI4SE/job_portal/src/backend
source .venv/bin/activate
alembic revision --autogenerate -m "create initial schema"
alembic upgrade head
```

- `revision --autogenerate`: so sánh SQLAlchemy metadata với database và tạo migration nháp.
- Phải đọc lại migration được sinh trước khi chạy.
- `upgrade head`: áp dụng tất cả migration chưa chạy.

Alembic chưa được cấu hình trong scaffold hiện tại; cần thêm dependency và cấu hình sau khi có SQLAlchemy models ban đầu.

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
