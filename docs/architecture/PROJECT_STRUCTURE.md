# Cấu trúc backend hiện hành

Dự án học tập dùng phân lớp nhẹ. Xem [BACKEND_GUIDE.md](BACKEND_GUIDE.md) để lần theo một API cụ thể.

```text
API routes + Pydantic DTO
    → Application services (quyền, validation nghiệp vụ, state machine)
        → Store executor (SQLAlchemy chỉ thực thi function)
            → SQL functions trong sql/
            → PostgreSQL
```

- `app/api/routes/`: nhận HTTP request, khai báo response và gọi hàm Python hoặc store đọc dữ liệu.
- `app/api/schemas.py`: DTO chung của các workflow tuần 4–6.
- `app/api/dependencies/`: database session và current user từ JWT.
- `app/application/<feature>/`: các hàm service viết theo từng chức năng, có thể Command-click từ route. Service được phép dùng SQLAlchemy và HTTPException trong kiến trúc học tập hiện tại.
- `app/application/common/`: kiểm tra quyền, chuyển ORM row thành dictionary, audit/notification chung.
- `app/infrastructure/persistence/models/`: định nghĩa bảng và constraint/index cho migration; không dùng ORM để đọc/ghi trong service.
- `app/infrastructure/persistence/stores.py`: gọi function bằng bind parameters; không sinh truy vấn trực tiếp lên bảng.
- `app/infrastructure/file_storage.py`: kiểm tra và ghi PDF vào private storage.
- `sql/`: toàn bộ thao tác dữ liệu, chia auth/session, company/job, profile/skills, resume/application, interview/offer, notification và development seed. Mỗi function có comment nêu mục đích và tham số; không chứa cả workflow nghiệp vụ lớn.
- `migrations/versions/`: thay đổi schema theo phiên bản.
- `migrations/sql/`: snapshot cố định của SQL tại thời điểm migration; không chỉnh sửa sau khi triển khai.
- `scripts/`: tạo admin, dữ liệu demo và gửi email SMTP tùy chọn.

Mọi CRUD và truy vấn dữ liệu đi qua stored function. Không cần một repository/interface cho từng bảng. Python service chỉ kiểm tra điều kiện và điều phối store trong transaction.

`domain/` và các `ports/` rỗng là scaffold cũ; chưa cần thêm lớp ở đó để triển khai những API này. Tài liệu kiến trúc MVP 5 tuần cũ chỉ là tham khảo, không phải nguồn định nghĩa schema hiện hành.

Đặt tên module Python bằng snake_case, store/schema database bằng snake_case. Comment phía trên function nêu mục đích và quyền của người gọi. Không nhận `user_id`, `created_by` hoặc quyền admin từ client khi có thể suy ra từ JWT.
