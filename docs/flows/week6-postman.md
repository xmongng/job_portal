# Chạy backend và kiểm tra đến tuần 6 bằng Postman

## Chuẩn bị trên máy chạy API

Từ `src/backend`:

```bash
source dev-env.sh  # Hoặc source .venv/bin/activate nếu không dùng PostgreSQL cài local
python -m pip install -e '.[dev]'
alembic upgrade head
python scripts/create_admin.py --email admin@example.com
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Nếu `.venv` được tạo bằng uv không có pip, dùng `uv pip install -e '.[dev]'` thay dòng pip. Đảm bảo PostgreSQL đang chạy và DATABASE_URL trỏ đúng database. JWT_SECRET phải có ít nhất 32 ký tự. Access token cũ thiếu `sid` cần đăng nhập lại.

`FILE_STORAGE_PATH` nên là đường dẫn private mà tài khoản chạy API ghi được. Mặc định mới là `src/backend/private-resumes`; `.env` đã có giá trị sẽ được ưu tiên, không bị sửa. Không public/static mount thư mục này.

## Collection

Import `docs/postman/JobPortal.postman_collection.json`. Chọn vai trò và token tương ứng cho từng nhóm; thay các biến ID bằng response thực tế. File CV cần tự chọn một PDF thật trong request multipart. Collection có login theo ba role và tự lưu token. Không cần đặt admin bằng API: tạo bằng CLI ở trên.

1. Đăng ký applicant, recruiter OWNER, recruiter MEMBER và một recruiter công ty khác. Tài khoản tự đăng ký không được role ADMIN.
2. Login từng role. POST refresh trả token mới; refresh token cũ nhận 401. Logout với refresh token hiện tại trả 204 và access token của phiên đó nhận 401 ngay. Các phiên khác không bị ảnh hưởng.
3. Recruiter tạo company. Admin xem và duyệt company. OWNER thêm recruiter đã đăng ký; MEMBER không được sửa company/quản lý membership.
4. Admin tạo skills. Recruiter tạo job DRAFT, submit. Admin approve/reject. Public API chỉ thấy PUBLISHED còn hạn thuộc company VERIFIED/ACTIVE. Recruiter công ty khác phải bị từ chối.
5. Applicant PUT profile, PUT skills, upload PDF, đặt default. CV lỗi/không phải PDF bị từ chối; vượt 5 MiB trả 413. User khác không download được CV.
6. Applicant apply bằng job và CV chính chủ. Apply trùng trả 409; resume_id của người khác bị từ chối. Application có bản sao file và metadata CV. Không xóa CV đang được application tham chiếu.
7. Recruiter xem đơn theo job, ghi note, chuyển SCREENING rồi INTERVIEW. Applicant không thấy recruiter_note, ghi chú lịch sử nội bộ hoặc storage_key. Không được nhảy thẳng từ APPLIED tới INTERVIEW/HIRED.
8. Schedule interview trong tương lai; thử lịch trùng/vòng trùng. Kết quả chỉ ghi khi đã tới giờ bắt đầu. Muốn thử toàn flow trong Postman, đặt lịch gần giờ hiện tại rồi chờ tới giờ trước khi gửi PASS/FAIL. Không có endpoint backdate để vượt điều kiện này.
9. Sau interview PASS và không còn lịch pending, recruiter tạo draft offer, send. Applicant mới nhìn thấy offer sau send. Chỉ applicant chính chủ accept/reject; accept đổi application sang HIRED. Mỗi application tối đa một offer active.
10. Thử offer hết hạn: quá response_deadline không accept được, `is_expired=true`, gọi expire để chuyển trạng thái EXPIRED. Có thể tạo offer mới sau expiry nếu application còn OFFER.
11. Thử withdraw/reject: history và notification được ghi; interview đang scheduled và offer đang pending bị hủy. Terminal application không đổi tiếp được.
12. User xem notifications của mình và đánh dấu đã đọc; user khác không thao tác được thông báo đó.

## Email tùy chọn

In-app notifications được lưu trong transaction nghiệp vụ. Email gửi sau commit qua worker, không làm rollback apply/interview/offer:

```bash
SMTP_ENABLED=true SMTP_HOST=localhost SMTP_PORT=1025 python scripts/send_notifications.py
```

Dùng SMTP local/MailHog đã cấu hình. Worker xử lý tối đa 50 thông báo/run, retry tối đa 5 lần; email `.invalid` của seed không được gửi. Chạy lại worker hoặc lập lịch trên máy triển khai nếu cần gửi định kỳ. Delivery là at-least-once; SMTP có thể nhận trùng nếu worker chết sau khi gửi trước lúc commit.

Frontend và AI/recommendations không thuộc phần tuần 6 này. Không đánh dấu những tính năng đó đã hoàn thành.
