# Đọc code backend từ đâu?

Backend đến tuần 6 gồm auth/session, company/membership, job approval, profile/skills, CV, application, interview, offer và thông báo. Không có frontend hoặc AI trong phạm vi này.

## Một API đi qua những file nào?

Ví dụ tạo công ty:

```text
POST /api/companies
  app/api/routes/recruitment.py → create_company()
  app/application/companies/service.py → create_company()
  infrastructure/persistence/stores.py → gọi function bằng bind parameters
  sql/company.sql → insert_company() + insert_company_membership()
  PostgreSQL → commit trước khi gửi response
```

Route nhận JSON và khai báo DTO. Service kiểm tra quyền và điều phối các bước. Mọi truy vấn/thao tác dữ liệu đều gọi store; model chỉ định nghĩa schema cho migration. Bạn có thể Command-click `companies.create_company` để đến hàm Python thực hiện nghiệp vụ.

Các API public và profile đã có vẫn dùng store, ví dụ:

```text
GET /api/companies
  app/api/routes/company.py → SELECT public.list_public_companies()
  sql/company.sql → định nghĩa SELECT
```

Tên function nằm trong chuỗi SQL nên Command-click thường không đến file SQL; tìm `CREATE OR REPLACE FUNCTION public.list_public_companies` trong project.

Mọi tương tác dữ liệu đều dùng store, cả API, tạo admin, seed và email worker. Python service giữ kiểm tra quyền, state machine và transaction. Mỗi store chỉ đọc/ghi một phần nhỏ và có comment tiếng Việt ngay trước CREATE FUNCTION.

Ví dụ Python:

```python
company = stores.one(db, "get_company_by_id", id=company_id)
```

Hàm này thực thi `SELECT * FROM public.get_company_by_id(p_id => :id)` bằng bind parameter. Định nghĩa function nằm trong `sql/company.sql`. Không có `db.add`, `db.get`, `select(Model)` hoặc SQL đọc/ghi bảng trực tiếp trong service.

## File cần sửa theo chức năng

| Chức năng | Route | Python nghiệp vụ | SQL dễ đọc |
|---|---|---|---|
| Auth | `api/routes/auth.py` | `application/auth/sessions.py`, `core/security.py` | `sql/auth.sql`, `sql/session.sql` |
| Company | `api/routes/company.py`, `api/routes/recruitment.py` | `application/companies/service.py` | `sql/company.sql` |
| Jobs | `api/routes/job.py`, `api/routes/recruitment.py` | `application/jobs/service.py` | `sql/job.sql` |
| Profile/skills | `api/routes/applicant.py`, `api/routes/skill.py` | `application/applicants/skills.py` | `sql/applicant.sql`, `sql/skill.sql` |
| CV | `api/routes/resume.py` | `application/resumes/service.py`, `infrastructure/file_storage.py` | `sql/resume.sql` |
| Applications | `api/routes/application.py` | `application/applications/service.py` | `sql/application.sql` |
| Interviews | `api/routes/pipeline.py` | `application/interviews/service.py` | `sql/interview.sql` |
| Offers | `api/routes/pipeline.py` | `application/offers/service.py` | `sql/offer.sql` |
| Notifications | `api/routes/pipeline.py` | `application/notifications/service.py` | `sql/notification.sql` |

Các đường dẫn trong bảng tính từ `src/backend/app/`, trừ `sql/` tính từ `src/backend/`.

## Transaction và trạng thái

Session là một transaction cho một request. Nếu bất kỳ bước nào lỗi, rollback cả thay đổi, history và notification. Dependency dùng scope `function` để commit xong trước khi response được gửi. Upload/apply có file ngoài database nên các route đó dọn file nếu commit thất bại.

- Job: `DRAFT → PENDING_APPROVAL → PUBLISHED → CLOSED`; admin có thể reject về `REJECTED`, recruiter sửa và submit lại.
- Application: `APPLIED → SCREENING → INTERVIEW → OFFER → HIRED`. Recruiter reject hoặc applicant withdraw trước terminal. Chỉ send offer tạo trạng thái OFFER; chỉ accept tạo HIRED.
- Interview: `SCHEDULED → COMPLETED/CANCELLED`. Lịch của cùng company hoặc cùng applicant không được chồng nhau; duration mặc định 60 phút.
- Offer: `DRAFT → SENT → ACCEPTED/REJECTED/EXPIRED`; withdrawal/rejection của application hủy offer pending thành CANCELLED. Offer quá deadline không accept được; endpoint expire cập nhật trạng thái lưu trữ.

Database dùng row lock, unique/check/FK và index để bảo vệ các invariant khi có request đồng thời. Việc khóa không thay thế kiểm tra quyền.

## Migration khác với file SQL đang học

`sql/` chứa các function nhỏ, chia theo chức năng để đọc và chỉnh sửa khi phát triển. `development.sql` chỉ phục vụ dữ liệu demo; không cần đọc file này khi học API company. Migration mới `c684d93ea201` tạo ba bảng history/audit và cập nhật constraint, sau đó cài các function từ snapshot trong `migrations/sql/`.

Migration `d927ac4106b8` bổ sung các store đọc/ghi thay cho ORM; SQL được chụp trong `migrations/sql/stores_v1/`.

Snapshot giữ nguyên để database mới luôn tái tạo được đúng phiên bản. Không sửa migration đã triển khai để nâng cấp database cũ: thêm migration mới.

Sau khi pull code này, chỉ cần `alembic upgrade head`; không cần chạy từng SQL thủ công. Trước khi chạy trên database có dữ liệu thật, sao lưu database. Migration không tự tạo tài khoản hoặc dữ liệu demo.
