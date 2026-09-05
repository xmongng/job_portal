# Software Requirements Specification

## Scope

Job Portal MVP hỗ trợ Admin, Recruiter và Applicant trong luồng đăng tin, duyệt tin, tìm việc, ứng tuyển, phỏng vấn và offer.

## Core acceptance criteria

- RBAC và resource-level authorization cho recruiter.
- Job: Draft → PendingApproval → Published/Rejected → Closed.
- Application: Applied → Screening → Interview → Offer → Hired; cho phép Rejected/Withdrawn hợp lệ.
- CV lưu private, allowlist PDF/DOC/DOCX, random filename và audit download.
- Chặn ứng tuyển trùng theo cặp applicant/job.
- Recommendation theo skill/location/salary; LLM chỉ giải thích match và soạn JD, luôn có fallback.
- Notification cho các thay đổi trạng thái quan trọng.
- Dashboard theo role, report và CSV export.

Chi tiết nghiệp vụ nguồn: `../phan-tich-bai-toan-job-portal-mvp.md` tại workspace ban đầu.
