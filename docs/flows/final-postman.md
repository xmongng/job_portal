# Postman: phần còn lại tuần 7–8

Tiếp tục sau [luồng auth → job → apply → interview → offer](week6-postman.md).

1. Pull code, cài dependencies theo `pyproject.toml`, chạy `alembic upgrade head` trên máy chạy API. Schema mới nhất là `e731ba6208c4`; không cần tạo lại database hoặc chạy từng SQL riêng.
2. Applicant có profile/skills gọi `GET /api/recommendations?limit=20&offset=0`. Chỉ job PUBLISHED còn hạn, company VERIFIED/ACTIVE được trả. Điểm tối đa 100: giao skills/job 70, location chính xác (không phân biệt hoa/thường) 15, mức lương đủ yêu cầu 15. Không có skill yêu cầu thì skill score = 0. Lương chưa khai báo không được tự coi là phù hợp.
3. Applicant gọi `POST /api/ai/jobs/{{jobId}}/explain`. `match.score` luôn do rule/store tính. AI chỉ giải thích facts và không có quyền cập nhật dữ liệu. Khi provider tắt, thiếu config, timeout, lỗi HTTP hoặc JSON không hợp lệ, trả explanation theo rule và `source=rules`.
4. Recruiter gọi `POST /api/ai/job-description` với title/category/location/employment_type/skills; luôn là draft cần review, không tạo job. Applicant gọi endpoint này trả 403.
5. Admin `GET /api/admin/users` có keyword/status/role/limit/offset. DTO không có password_hash/token. `PUT /api/admin/users/{{userId}}/status` để SUSPENDED hoặc ACTIVE. Suspend thu hồi mọi session; activate không phục hồi token cũ. Không tự suspend admin đang gọi.
6. Admin `PUT /api/admin/companies/{{companyId}}/status` để SUSPENDED/ACTIVE. Company bị suspend khiến job public ẩn và recruiter mất quyền thay đổi nghiệp vụ company đó. Verification_status được xử lý riêng bằng API review hiện có.
7. Admin `GET /api/reports/summary` xem toàn hệ thống; recruiter bắt buộc `?company_id={{companyId}}` chính chủ. Applicant hoặc recruiter company khác trả 403. `GET /api/reports/export.csv` xuất số liệu aggregate (không chứa email/note/CV).
8. Admin `GET /api/admin/audit-logs` xem audit phân trang. Applicant/recruiter bị từ chối.
9. Kiểm tra 401 khi thiếu/hết hạn token, 422 UUID/body sai, 409 unique/state sai, 413 upload vượt 5 MiB. Register từ chối field ngoài allowlist và không cho ADMIN.
10. Login/register/refresh giới hạn mặc định 30 request/phút/IP, AI 10 request/phút/IP. Vượt trả 429 + Retry-After. Giới hạn trong bộ nhớ một process, không phải distributed limiter. Khi test Collection Runner có thể tăng biến môi trường hợp lý cho môi trường test.

## AI configuration

Mặc định `AI_PROVIDER=none`, hệ thống hoạt động đủ khi không có API key. Cấu hình tùy chọn:

```env
AI_PROVIDER=gemini
AI_API_KEY=<private key>
AI_MODEL=<model hỗ trợ generateContent và JSON output>
AI_TIMEOUT_SECONDS=10
```

Implementation dùng Gemini generateContent qua httpx theo [API chính thức](https://ai.google.dev/api/generate-content). Model do người triển khai chọn; không hard-code một tên có thể ngừng hỗ trợ. Không hỗ trợ provider khác trong bản này. Token/API key không được đưa vào Git. Live API không được gọi trong test tự động; test dùng HTTP mock cho success/timeout/invalid response.

Chỉ facts của match (skill names, job title và score) hoặc input JD allowlist đi tới provider. Không gửi email/tên thật, hồ sơ education/experience, file CV, token, password/hash hoặc recruiter notes. Output AI là nội dung không tin cậy; frontend tương lai phải render như text và yêu cầu recruiter review trước khi dùng.

## Bàn giao

- Swagger `/docs`, schema `/openapi.json`, Postman collection trong `docs/postman/`.
- Hướng dẫn deployment, CORS, host và backup/restore: `docs/deployment/DEPLOYMENT.md`.
- Các test với PostgreSQL chỉ chạy khi `TEST_DATABASE_URL` trỏ tới database riêng có hậu tố `_test`; rollback dữ liệu và dùng file tạm. CI cấu hình PostgreSQL test tự động.
- Không coi deploy production là đã hoàn thành chỉ vì code đã push. Người triển khai vẫn cần domain/HTTPS, secrets và nghiệm thu môi trường thật.
