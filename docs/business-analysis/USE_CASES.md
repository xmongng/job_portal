# Use cases cốt lõi — Job Portal backend

Tài liệu này khớp với schema 14 bảng trong [ERD.md](../database/ERD.md).

| Mã | Use case | Bảng chính |
|---|---|---|
| UC-01 | Đăng ký, đăng nhập, refresh, logout | users, auth_sessions |
| UC-02 | Tạo/cập nhật công ty | companies, company_memberships |
| UC-03 | Thêm recruiter vào công ty | users, company_memberships |
| UC-04 | Tạo/sửa/đăng/đóng job | jobs, job_skills, skills |
| UC-05 | Xem danh sách và chi tiết job công khai | jobs, companies |
| UC-06 | Cập nhật hồ sơ và kỹ năng ứng viên | applicants, applicant_skills, skills |
| UC-07 | Upload và chọn CV | resumes, applicants |
| UC-08 | Ứng tuyển và rút đơn | applications, jobs, resumes |
| UC-09 | Recruiter xử lý application | applications, company_memberships |
| UC-10 | Tạo và cập nhật phỏng vấn | interviews, applications |
| UC-11 | Tạo và phản hồi offer | offers, applications |
| UC-12 | Đọc thông báo | notifications, users |
| UC-13 | Gợi ý job theo kỹ năng | applicant_skills, job_skills, jobs |
| UC-14 | AI giải thích match/soạn JD | đọc applicants, skills, jobs; không cần bảng AI |

## Quy tắc authorization

- API public chỉ trả company `VERIFIED/ACTIVE` và job `PUBLISHED` còn hạn.
- Recruiter phải có `company_memberships` phù hợp trước khi sửa company, job hoặc application.
- `OWNER` quản lý thành viên; `MEMBER` quản lý nghiệp vụ tuyển dụng.
- Applicant chỉ sửa hồ sơ, CV và application của chính mình.
- Admin được duyệt company và hỗ trợ quản lý dữ liệu danh mục.

## Trạng thái chính

```text
Job: DRAFT -> PUBLISHED -> CLOSED

Application: APPLIED -> INTERVIEW -> OFFER -> HIRED
             |            |          |
             +----------> REJECTED <-+
             +----------> WITHDRAWN

Interview: SCHEDULED -> COMPLETED/CANCELLED
Offer: DRAFT -> SENT -> ACCEPTED/REJECTED
```

State transition được kiểm tra trong application service. Database dùng check constraint để từ chối giá trị trạng thái không hợp lệ.
