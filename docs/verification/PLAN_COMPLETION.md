# Phạm vi hoàn thiện backend theo master plan

Nguồn: Master_Plan.xlsx đã đối chiếu trong phiên trước (8 tuần, backend only); bản trong Downloads không còn ở đường dẫn cũ tại thời điểm cập nhật này. Không sửa trạng thái hay tỷ lệ hoàn thành của workbook.

| Tuần | Code/deliverable |
|---|---|
| 1–2 | Vai trò, tài liệu, PostgreSQL models/constraint, migrations, seed và hướng dẫn psql |
| 3 | Public company/jobs, register/login, JWT current user, DTO/filter/pagination |
| 4 | Refresh/logout, membership/owner, phân quyền resource, submit/approve/reject/close job và history |
| 5 | Profile/education/experience/skills, PDF private/default/delete/download, apply snapshot/duplicate/withdraw |
| 6 | Recruiter pipeline/note, interview schedule/cancel/result/conflict, offer lifecycle/expiry, in-app và worker SMTP tùy chọn |
| 7 | Rule-based recommendation, AI explanation/JD với timeout/fallback, admin user/company moderation, reports/CSV |
| 8 | PostgreSQL integration workflow + unit/security/provider tests, Postman, CORS/hosts/rate limit/log, production Compose, backup/restore scripts và tài liệu bàn giao |

Mọi thao tác dữ liệu runtime qua stored functions trong `src/backend/sql/`. Mỗi function có comment ở đầu. Python service kiểm tra quyền/lifecycle và transaction; migration lưu snapshot SQL. Seed/admin/email worker cũng gọi store; SQL trực tiếp trong test chỉ phục vụ setup/điều chỉnh đồng hồ/cleanup của database test.

## Bằng chứng và giới hạn

Kiểm tra trên cluster PostgreSQL tạm, không nâng cấp database chính: clean migration, full recruitment through offer, rule score, AI fallback, role/resource/privacy, account/company suspension, aggregate CSV, rotation/logout, middleware/rate limit, provider HTTP mock, schema/model parity, migration downgrade/upgrade và backup/restore riêng biệt.

Không gọi paid/live AI, không gửi SMTP thật, không triển khai production hoặc sửa credentials. Production Docker build/runtime và live TLS/domain cần nghiệm thu trên máy triển khai. File workbook gốc không được cập nhật tự động; không tuyên bố các nghiệm thu hạ tầng thật đã hoàn tất.

AI hiện hỗ trợ `none`/`gemini`; default `none`. Recommendation không dùng LLM. AI drafts không tự lưu job hoặc quyết định tuyển dụng. Email là worker at-least-once tùy chọn, không phải hàng đợi distributed.

## Kết quả kiểm tra của lần cập nhật này

- `pytest -q` với PostgreSQL test riêng: **7 passed**. Full-workflow test chứa các request success/denied/invalid-state từ register tới HIRED và các API tuần 7; đây là số test functions, không phải tổng số requests.
- Refresh đồng thời: một request thành công, một replay nhận 401.
- `alembic check`: không phát hiện lệch model/schema.
- Clean upgrade và downgrade/upgrade revision tuần 7: đạt.
- pg_dump/pg_restore vào database `_restore` mới: đạt.
- Ruff, git diff whitespace và Compose local/production validation: đạt.
- Docker daemon tắt nên chưa xác minh image build/runtime.
- AI mock success/timeout/invalid-output và fallback: đạt; chưa gọi provider thật.
- Tất cả store mới được gọi và có comment đầu hàm; migration là frozen snapshot, không phải code dư.
