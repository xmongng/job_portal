# Software Requirements Specification — Backend học tập

## Phạm vi

Job Portal backend hỗ trợ ba vai trò `ADMIN`, `RECRUITER`, `APPLICANT` và tập trung vào việc học thiết kế REST API, validation, authorization, transaction, truy vấn PostgreSQL và tích hợp AI cơ bản.

## Chức năng cốt lõi

- Đăng nhập, refresh và logout bằng `users`/`auth_sessions`.
- Công ty có nhiều recruiter thông qua `company_memberships`.
- Recruiter tạo, sửa, đăng và đóng job thuộc công ty của mình.
- Khách xem công ty và job công khai.
- Applicant quản lý hồ sơ, kỹ năng và CV.
- Applicant ứng tuyển một lần cho mỗi job.
- Recruiter cập nhật application, tạo interview và offer.
- Người dùng đọc thông báo trong ứng dụng.
- Gợi ý job theo rule và dùng AI để giải thích độ phù hợp hoặc soạn JD.

## Ngoài phạm vi hiện tại

- Xác thực email/quên mật khẩu, hàng đợi email và invitation token.
- Audit log đầy đủ, lịch sử mọi lần đổi trạng thái và distributed rate limit.
- Thanh toán, chat, microservices và hệ thống AI tự ra quyết định.

## Tiêu chí tối thiểu

- API dùng DTO allowlist và truy vấn có bind parameter.
- Recruiter chỉ sửa dữ liệu thuộc công ty mình tham gia.
- Applicant không xem recruiter note hoặc dữ liệu nội bộ.
- File CV được kiểm tra loại/dung lượng và lưu ngoài database.
- Các thao tác nhiều bước chạy trong một transaction.
- AI có fallback, không nhận mật khẩu/token/CV file và không tự cập nhật trạng thái.
