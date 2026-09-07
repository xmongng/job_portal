# PHÂN TÍCH BÀI TOÁN — JOB PORTAL (MVP 5 TUẦN)
### Bản điều chỉnh từ tài liệu kiến trúc gốc + Design System màu sắc

> Tài liệu này **điều chỉnh lại** bản phân tích/kiến trúc gốc (`job_portal_analysis_architecture.md`) để vừa khít mốc **5 tuần**, đảm bảo *mọi chức năng cơ bản của đề bài đều chạy được thật*, có **AI tích hợp cơ bản**, và bổ sung **bảng màu/giao diện chuyên nghiệp, tươi sáng** mà bản gốc chưa có. Đi kèm với file `cau-truc-du-an-job-portal-mvp.md` (cấu trúc thư mục source code tương ứng).

---

# 0. Đánh giá: tài liệu gốc đã đủ cho MVP 5 tuần chưa?

**Trả lời: Chưa phù hợp nếu giữ nguyên 100%.** Tài liệu gốc là một bản thiết kế ở mức "production-grade" rất đầy đủ (92 mục, hơn 4.600 dòng) — chất lượng kỹ thuật tốt, đúng bài bản Clean Architecture — nhưng **khối lượng công việc lớn hơn nhiều** so với những gì có thể hoàn thành **chắc chắn** trong 5 tuần, đặc biệt nếu bạn làm một mình hoặc nhóm 2 người.

## 0.1. Những gì nên giữ nguyên (đã tốt, không cần sửa)

- Kiến trúc **Modular Monolith + Clean Architecture nhẹ** (Domain/Application/Infrastructure/Api) — phù hợp quy mô đồ án, không over-engineer.
- Toàn bộ **state machine** của Job và Application (Draft → PendingApproval → Published; Applied → Screening → Interview → Offer → Hired/Rejected).
- Cách tiếp cận **AI không cần vector DB**: recommendation bằng rule-based scoring + LLM chỉ dùng cho 2 việc nhỏ (giải thích match, hỗ trợ viết JD). Đây là điểm rất đúng — nhiều đồ án sinh viên sa đà vào AI phức tạp (embedding, fine-tune) và không kịp làm nghiệp vụ chính.
- Nguyên tắc bảo mật CV: private storage, allowlist định dạng, random filename, download có kiểm tra quyền, audit khi tải CV.
- Tech stack: Python + FastAPI + PostgreSQL + React/TS/Vite.

## 0.2. Vấn đề khi áp vào mốc 5 tuần

| Vấn đề | Chi tiết |
|---|---|
| **Không có lộ trình theo tuần** | Bản gốc chia 9 "Phase" nhưng không gắn số tuần cụ thể, và giả định **team 4 người** làm song song (mục 73) — không hợp nếu bạn làm một mình hoặc nhóm nhỏ hơn. |
| **Khối lượng NFR quá lớn cho 5 tuần** | 2FA, Redis cache, rate limiting chuẩn production, structured logging, optimistic concurrency/versioning, seed ≥ 2.000 dòng, test coverage 30–40%, CI/CD 2 workflow — mỗi mục đều tốn thời gian đáng kể mà không làm ứng dụng "chạy được" nhanh hơn. |
| **Thiếu hoàn toàn Design System** | Không có bảng màu, typography, khoảng cách (spacing) — trong khi bạn yêu cầu rõ "màu sắc chuyên nghiệp, dùng màu sáng để người dùng cảm thấy dễ chịu". |
| **Một số phần vượt mức "cơ bản"** | Multi-round interview với business rule chi tiết, LLM cost-control nâng cao, phòng chống prompt-injection, bảng background_jobs riêng — tốt cho production nhưng chưa phải ưu tiên khi chức năng cơ bản còn chưa xong. |

**→ Kết luận:** giữ lại toàn bộ nghiệp vụ cốt lõi và kiến trúc chính, nhưng **cắt gọn phần hạ tầng/NFR nặng**, bổ sung **lộ trình theo tuần** và **bảng màu**. Chi tiết cắt giảm ở mục 6.

---

# 1. Tổng quan bài toán (rút gọn)

Job Portal kết nối 3 vai trò:

1. **Admin** — duyệt tin tuyển dụng, quản lý công ty/tài khoản, xem báo cáo toàn hệ thống.
2. **Nhà tuyển dụng (Recruiter)** — quản lý công ty, đăng tin, theo dõi ứng viên theo pipeline, lên lịch phỏng vấn, tạo offer.
3. **Ứng viên (Applicant)** — tạo hồ sơ, quản lý CV, tìm việc, ứng tuyển, theo dõi trạng thái, nhận gợi ý việc làm.

Luồng nghiệp vụ trung tâm — cũng là luồng demo chính:

```text
Recruiter tạo Job (Draft)
      ↓
Submit → Pending Approval
      ↓
Admin Approve / Reject
      ↓
Published (hiện công khai)
      ↓
Applicant tìm kiếm → Apply (chọn CV)
      ↓
Applied → Screening → Interview → Offer → Hired
                    ↘ Rejected (ở bất kỳ bước nào)
      ↓
Notification xuyên suốt mỗi lần đổi trạng thái
```

---

# 2. Chức năng chi tiết theo vai trò — ai làm gì, chức năng đó làm gì

## 2.1. Admin

| Chức năng | Mô tả cụ thể |
|---|---|
| Duyệt tin tuyển dụng | Xem danh sách job có trạng thái `PendingApproval`, xem chi tiết, **Approve** (job chuyển `Published`, ghi `approved_by`, `published_at`, gửi notification cho recruiter) hoặc **Reject** (kèm lý do, gửi notification). |
| Quản lý công ty | Xem/khóa/mở công ty; xem danh sách recruiter thuộc công ty. |
| Quản lý người dùng | Xem danh sách user theo role, khóa/mở tài khoản vi phạm. |
| Báo cáo tổng | Xem số liệu: tổng số tin đăng theo trạng thái, tổng số ứng viên, tổng số ứng tuyển theo thời gian (biểu đồ + bảng, export CSV). |
| Audit tối thiểu | Xem log các hành động nhạy cảm: ai duyệt job nào, ai tải CV nào — phục vụ minh bạch, không cần lịch sử version đầy đủ. |

## 2.2. Nhà tuyển dụng (Recruiter)

| Chức năng | Mô tả cụ thể |
|---|---|
| Quản lý công ty của mình | Tạo/sửa thông tin công ty (tên, mô tả, logo, địa chỉ); một công ty có thể có nhiều recruiter, mỗi recruiter **chỉ thao tác được trên job/ứng viên thuộc công ty mình** (resource-level authorization — bắt buộc, không chỉ role-level). |
| Đăng/sửa tin tuyển dụng | Tạo job ở trạng thái `Draft` (tiêu đề, mô tả, yêu cầu, kỹ năng cần — chọn từ danh sách skill có sẵn, mức lương, địa điểm, hạn nộp); **Submit** để gửi Admin duyệt. |
| Xem pipeline ứng viên theo job | Danh sách ứng viên đã apply cho một job, lọc theo trạng thái (Applied/Screening/Interview/Offer/Hired/Rejected), xem hồ sơ + CV (có audit khi tải CV). |
| Cập nhật trạng thái ứng tuyển | Chuyển trạng thái theo đúng state machine (không cho nhảy bước tuỳ ý, ví dụ không thể từ `Applied` nhảy thẳng lên `Hired`), mỗi lần chuyển ghi vào `application_status_history`. |
| Lên lịch phỏng vấn | Tạo lịch phỏng vấn (ngày giờ, hình thức online/offline, vòng thứ mấy), ghi kết quả/feedback sau phỏng vấn. |
| Tạo & theo dõi Offer | Tạo offer (mức lương, ngày bắt đầu, hạn phản hồi/deadline), theo dõi trạng thái Sent/Accepted/Rejected/Expired. |
| Dashboard pipeline | Xem tổng quan dạng Kanban đơn giản: số ứng viên ở mỗi cột trạng thái, theo từng job hoặc toàn công ty. |

## 2.3. Ứng viên (Applicant)

| Chức năng | Mô tả cụ thể |
|---|---|
| Hồ sơ cá nhân | Cập nhật thông tin cá nhân, học vấn, kinh nghiệm, và **danh sách kỹ năng** (chọn từ danh sách skill chuẩn hoá — dùng để search & recommend). |
| Quản lý CV | Upload nhiều CV (PDF/DOC/DOCX, giới hạn dung lượng), đặt CV mặc định, xoá CV (soft-delete nếu đã từng được dùng để apply). |
| Tìm việc | Tìm theo từ khoá (tên job, mô tả) kết hợp filter theo kỹ năng, địa điểm, mức lương; chỉ hiển thị job `Published`. |
| Ứng tuyển | Chọn 1 CV cụ thể để nộp cho 1 job; hệ thống **chặn ứng tuyển trùng** (1 applicant chỉ apply 1 lần/job); lưu CV nào đã dùng tại thời điểm apply (snapshot tham chiếu). |
| Theo dõi trạng thái | Xem trạng thái từng đơn ứng tuyển theo thời gian thực, xem lịch sử chuyển trạng thái. |
| Lịch phỏng vấn | Xem lịch phỏng vấn được mời, nhận notification nhắc lịch. |
| Nhận & phản hồi Offer | Xem chi tiết offer, Accept hoặc Reject trước hạn deadline. |
| Gợi ý việc làm (AI cơ bản) | Xem danh sách job được gợi ý dựa trên độ khớp kỹ năng/hồ sơ (xem mục 5). |
| Thông báo | Nhận thông báo trong ứng dụng (và email cơ bản) khi: job được duyệt/apply thành công/trạng thái đổi/có lịch phỏng vấn/có offer. |

---

# 3. Dữ liệu chính — rút gọn cho 5 tuần

Giữ đúng 8 entity theo đề bài, bổ sung tối thiểu bảng phụ cần thiết để chạy đúng nghiệp vụ (không thêm bảng cho tính năng bị cắt ở mục 6):

```text
users                     (auth: id, email, password_hash, role, is_active)
companies                 (id, name, description, logo_url, owner tổng)
company_recruiters        (company_id, user_id) — 1 công ty nhiều recruiter
skills                    (id, name)
jobs                      (id, company_id, title, description, salary, location,
                           status: Draft|PendingApproval|Published|Rejected|Closed,
                           approved_by, published_at, deadline)
job_skills                (job_id, skill_id)
applicants                (user_id, full_name, headline, education, experience)
applicant_skills          (applicant_id, skill_id)
resumes                   (id, applicant_id, file_key, original_name, is_default)
applications              (id, job_id, applicant_id, resume_id, status, applied_at)
application_status_history(application_id, from_status, to_status, changed_by, changed_at)
interviews                (id, application_id, round_number, scheduled_at, mode, result, feedback)
offers                    (id, application_id, salary, start_date, deadline, status)
notifications             (id, user_id, type, content, is_read, created_at)
audit_logs                (tối giản: user_id, action, entity, entity_id, created_at)
refresh_tokens            (tối giản, không cần rotation phức tạp cho 5 tuần)
```

**Đã bỏ so với bản gốc** (xem lý do đầy đủ ở mục 6): bảng `background_jobs` riêng, bảng version/audit chi tiết cho từng entity, các bảng phục vụ 2FA/OAuth.

---

# 4. Tích hợp AI cơ bản — làm gì và làm như thế nào trong 5 tuần

Đề bài chỉ yêu cầu "gợi ý việc làm theo hồ sơ" — **không bắt buộc dùng LLM** cho phần này. Cách tiếp cận đúng đắn và khả thi trong 5 tuần là **chia làm 3 tính năng nhỏ, độc lập, dễ demo**:

### 4.1. Gợi ý việc làm — Rule-based (không cần LLM, không cần train model)

- Công thức điểm phù hợp đơn giản:
  ```text
  score = 0.6 × (số skill trùng / số skill job yêu cầu)
        + 0.25 × (cùng địa điểm ? 1 : 0)
        + 0.15 × (mức lương mong muốn nằm trong range job ? 1 : 0)
  ```
- Chạy bằng một truy vấn SQL join `applicant_skills` với `job_skills`, sắp xếp giảm dần theo `score`, trả top N job `Published`.
- Đây **là AI theo nghĩa hệ gợi ý (recommender system)** — hoàn toàn hợp lệ để tính là "tích hợp AI cơ bản", làm được trong 1–2 ngày, không rủi ro về chi phí/API.

### 4.2. AI giải thích độ phù hợp — dùng LLM thật (OpenAI/Gemini API)

- Khi ứng viên mở chi tiết 1 job, gọi 1 request tới LLM với **prompt chỉ chứa dữ liệu đã ẩn danh hoá tối thiểu**: danh sách skill ứng viên có (dạng tag), danh sách skill job yêu cầu, tên job — **không gửi CV gốc, không gửi PII** (tên, email, số điện thoại).
- LLM trả về đoạn văn ngắn 2–3 câu: vì sao phù hợp/chưa phù hợp + gợi ý nên bổ sung kỹ năng gì.
- **Cache theo cặp (applicant_id, job_id)** để không gọi lại API nhiều lần cho cùng 1 cặp — tiết kiệm chi phí và thời gian phản hồi.
- **Fallback bắt buộc**: nếu LLM lỗi/hết hạn mức → hiển thị "Chưa có gợi ý AI lúc này", **không được chặn** luồng xem job/ứng tuyển.

### 4.3. AI hỗ trợ soạn mô tả công việc (JD Assistant) — cho Recruiter

- Recruiter nhập: chức danh, vài gạch đầu dòng yêu cầu, mức lương (tuỳ chọn) → bấm "Soạn JD bằng AI" → LLM sinh bản mô tả đầy đủ (Mô tả công việc / Yêu cầu / Quyền lợi) → recruiter **chỉnh sửa lại** trước khi Submit.
- AI **không bao giờ tự động đăng job** hay tự động duyệt/loại ứng viên — chỉ hỗ trợ soạn thảo, con người luôn là người quyết định cuối cùng.

### 4.4. Nguyên tắc kỹ thuật chung

- Gọi LLM qua `fetch` phía server — không cần thêm SDK lớn.
- Tạo một interface `AiAssistant` trong Application layer, implement thật ở Infrastructure — để dễ đổi provider hoặc mock khi test, và dễ tắt AI hoàn toàn nếu hết thời gian mà không ảnh hưởng phần còn lại của hệ thống.
- Giấu API key trong biến môi trường, không log nội dung prompt/response có thể chứa dữ liệu nhạy cảm.

---

# 5. Cắt giảm khỏi bản gốc để vừa 5 tuần

| Hạng mục trong bản gốc | Quyết định cho 5 tuần | Lý do |
|---|---|---|
| 2FA | Bỏ (để bonus nếu dư thời gian) | Không phải chức năng bắt buộc của đề bài |
| Redis cache | Bỏ, hoặc thêm cuối tuần 5 nếu dư thời gian | Dữ liệu demo nhỏ, chưa cần cache để đạt hiệu năng |
| Elasticsearch / pgvector / vector DB | Bỏ hẳn | Chính bản gốc cũng khuyến nghị không cần |
| Seed ≥ 2.000 record | Giảm còn ~200–300 record | Đủ để demo tìm kiếm/pagination/dashboard có dữ liệu, không cần độ lớn production |
| Test coverage 30–40% | Chuyển thành "test các luồng nghiệp vụ chính" (auth, approve job, apply, đổi trạng thái) | Ưu tiên tính năng chạy đúng hơn là đạt % coverage |
| CSV/Excel export đầy đủ | Giữ CSV cho báo cáo, PDF cho **CV template** (đề bài có yêu cầu riêng mục này), bỏ Excel nếu thiếu thời gian | CSV nhanh làm, đủ đáp ứng "báo cáo số tin/số ứng viên" |
| Audit log & versioning/optimistic concurrency chi tiết | Giữ audit tối thiểu (ai duyệt job, ai tải CV) | Đề bài chỉ yêu cầu "bảo mật file CV, phân quyền xem hồ sơ", không yêu cầu lịch sử version |
| Bảng `background_jobs` riêng + BackgroundService phức tạp | Gửi email/notification xử lý đồng bộ hoặc hàng đợi trong bộ nhớ đơn giản | Khối lượng thao tác nhỏ trong demo, chưa cần hệ thống job production |
| Rate limiting/CORS/logging chuẩn production | Giữ ở mức cơ bản dùng middleware FastAPI | Vẫn có, nhưng không đầu tư sâu thêm |
| Multi-round interview với business rule phức tạp | 1 bảng `interviews` có `round_number` là đủ | Đủ minh chứng "hỗ trợ nhiều vòng phỏng vấn" |
| CI/CD 2 workflow build/deploy riêng | 1 workflow CI: build + test cơ bản | Đủ minh chứng automation |
| Docker Compose 5 service | Rút còn 3 service bắt buộc (`api`, `web`, `postgres`), Mailhog/Redis optional | Giảm thời gian setup hạ tầng |
| LLM cost-control nâng cao, phòng prompt-injection chi tiết | Giữ nguyên tắc cơ bản (không gửi PII, có fallback, cache) | Đủ an toàn cho quy mô đồ án |

> Toàn bộ các mục bị cắt vẫn **hoàn toàn có thể làm thêm** nếu 5 tuần hoàn thành sớm — coi đây là backlog P1/P2 (mục 8).

---

# 6. Lộ trình 5 tuần chi tiết

*Giả định: 1 người hoặc nhóm nhỏ 2–3 người, làm việc gần như toàn thời gian. Mỗi tuần kết thúc bằng một bản demo được (không phải "code xong nhưng chưa chạy").*

## Tuần 1 — Nền tảng + Auth/RBAC + Company/Job cơ bản
- Ngày 1–2: khởi tạo repo, Docker Compose tối giản, backend Python/FastAPI phân lớp, frontend Vite+React+TS+Tailwind (áp bảng màu ở mục 7 ngay từ đầu), thiết kế schema DB rút gọn (mục 3) + migration đầu tiên.
- Ngày 3–4: đăng ký/đăng nhập/JWT + refresh token đơn giản, 3 role, middleware phân quyền, seed 3 tài khoản demo (admin/recruiter/applicant).
- Ngày 5: Company CRUD, Job CRUD (Draft), state machine Job, màn hình Admin duyệt job.
- **Bàn giao:** đăng nhập 3 role hoạt động; recruiter tạo job → admin duyệt → job Published.

## Tuần 2 — Tìm kiếm + Hồ sơ ứng viên + CV
- Ngày 1–2: trang danh sách job public, tìm kiếm theo từ khoá + filter theo skill/địa điểm, pagination.
- Ngày 3: hồ sơ ứng viên (thông tin cá nhân + kỹ năng).
- Ngày 4–5: upload CV (private storage, allowlist định dạng, giới hạn size, random filename), API download có kiểm tra quyền sở hữu + ghi audit.
- **Bàn giao:** ứng viên có hồ sơ + nhiều CV; tìm kiếm job hoạt động đúng.

## Tuần 3 — Application Pipeline
- Ngày 1–2: chức năng Apply (chọn CV, chặn apply trùng), ghi `application_status_history`.
- Ngày 3–4: màn hình pipeline cho recruiter (đổi trạng thái theo state machine), màn hình "Đơn ứng tuyển của tôi" cho applicant.
- Ngày 5: Notification cơ bản (in-app + email đơn giản qua SMTP/MailHog khi đổi trạng thái quan trọng).
- **Bàn giao:** luồng Applied → Screening chạy đầy đủ, có lịch sử trạng thái + thông báo.

## Tuần 4 — Interview + Offer + AI cơ bản
- Ngày 1–2: lên lịch phỏng vấn (nhiều vòng đơn giản), ghi kết quả/feedback.
- Ngày 3: Offer (tạo, deadline, accept/reject của ứng viên).
- Ngày 4–5: tích hợp AI — (1) rule-based recommendation, (2) AI giải thích match qua LLM, (3) AI JD assistant cho recruiter.
- **Bàn giao:** luồng Apply → Interview → Offer chạy end-to-end; có gợi ý việc làm + AI giải thích.

## Tuần 5 — Dashboard, Report, hoàn thiện & demo
- Ngày 1–2: dashboard theo role (Admin: tổng số job/company/user; Recruiter: pipeline dạng Kanban đơn giản; Applicant: tổng quan đơn ứng tuyển).
- Ngày 3: báo cáo số tin/số ứng viên (bảng + biểu đồ Recharts, export CSV), CV template PDF.
- Ngày 4: viết test cho các luồng quan trọng nhất (auth, apply, approve job, đổi trạng thái) — không chạy theo % coverage.
- Ngày 5: polish UI theo Design System, seed dữ liệu demo (200–300 record), chuẩn bị kịch bản demo (mục 9).
- **Bàn giao:** sản phẩm hoàn chỉnh chức năng cơ bản + AI cơ bản + giao diện chuyên nghiệp, sẵn sàng demo.

---

# 7. Design System — Bảng màu & giao diện chuyên nghiệp, tươi sáng

**Nguyên tắc:** nền sáng (light theme), màu chủ đạo là **xanh dương tin cậy** (đúng tinh thần "tuyển dụng — kết nối — chuyên nghiệp", tương tự LinkedIn/Indeed), các màu trạng thái dùng **tông nhạt/pastel cho nền badge** thay vì màu đặc để tạo cảm giác nhẹ nhàng, dễ chịu, không gây mỏi mắt khi dùng lâu (đúng phong cách các dashboard SaaS hiện đại như Stripe, Linear, Notion).

## 7.1. Bảng màu chính (Core Palette)

| Vai trò | Tên biến | Hex | Dùng ở đâu |
|---|---|---|---|
| Primary | `--color-primary` | `#2563EB` | Nút chính, link, icon active, header |
| Primary hover | `--color-primary-hover` | `#1D4ED8` | Hover/active state của nút primary |
| Primary tint (nền nhạt) | `--color-primary-50` | `#EFF6FF` | Nền banner, nền hover nhẹ, badge "Published" |
| Secondary/Accent | `--color-accent` | `#10B981` | Nút thành công, badge "Hired", biểu tượng tích cực |
| Accent tint | `--color-accent-50` | `#ECFDF5` | Nền badge "Hired/Accepted" |
| Nền trang | `--color-bg` | `#F8FAFC` | Nền toàn trang (không dùng trắng thuần để đỡ chói) |
| Nền card/surface | `--color-surface` | `#FFFFFF` | Card, bảng, modal |
| Viền | `--color-border` | `#E2E8F0` | Border card, input, divider |
| Chữ chính | `--color-text` | `#0F172A` | Tiêu đề, nội dung chính |
| Chữ phụ | `--color-text-muted` | `#64748B` | Mô tả phụ, placeholder, timestamp |

## 7.2. Bảng màu trạng thái (Status Badges) — dùng tông nhạt cho nền, tông đậm cho chữ

| Trạng thái | Nền (bg) | Chữ (text) | Ý nghĩa |
|---|---|---|---|
| Draft | `#F1F5F9` | `#64748B` | Đang soạn thảo |
| Pending Approval | `#FEF3C7` | `#B45309` | Chờ admin duyệt |
| Published | `#EFF6FF` | `#1D4ED8` | Đã công khai |
| Rejected (job) / Rejected (application) | `#FEE2E2` | `#B91C1C` | Bị từ chối |
| Applied | `#EFF6FF` | `#2563EB` | Vừa nộp đơn |
| Screening | `#FEF3C7` | `#B45309` | Đang sàng lọc |
| Interview | `#EDE9FE` | `#6D28D9` | Đang phỏng vấn |
| Offer | `#CCFBF1` | `#0F766E` | Đã gửi offer |
| Hired | `#ECFDF5` | `#047857` | Trúng tuyển |
| Withdrawn/Closed | `#F1F5F9` | `#64748B` | Đã đóng/rút đơn |

## 7.3. Typography

- Font chữ: **Inter** (hoặc **Plus Jakarta Sans** cho tiêu đề nếu muốn nhấn mạnh hơn) — miễn phí trên Google Fonts, hiện đại, chuyên nghiệp, dễ đọc trên mọi kích thước màn hình.
- Cỡ chữ gợi ý: H1 `28px/700`, H2 `22px/600`, H3 `18px/600`, Body `14–15px/400`, Caption `12px/400` màu `--color-text-muted`.

## 7.4. Bo góc, khoảng cách, đổ bóng

- Bo góc: `8px` cho input/button, `12px` cho card, `16px` cho modal — tạo cảm giác mềm mại, hiện đại, không quá vuông vức "cứng nhắc".
- Khoảng cách: hệ số 4px (4/8/12/16/24/32) — dùng nhất quán toàn bộ giao diện.
- Đổ bóng: chỉ dùng bóng rất nhẹ cho card (`box-shadow: 0 1px 3px rgba(15,23,42,0.06)`), tránh bóng đậm gây rối mắt.

## 7.5. Ví dụ áp dụng

- **Nút Primary:** nền `#2563EB`, chữ trắng, hover `#1D4ED8`, bo góc `8px`.
- **Nút Secondary/Outline:** nền trắng, viền `#E2E8F0`, chữ `#0F172A`, hover nền `#F8FAFC`.
- **Banner trang chủ (hero):** gradient nhẹ `linear-gradient(135deg, #2563EB 0%, #4F46E5 100%)` — chỉ dùng ở khu vực nhỏ (hero/CTA), phần còn lại của trang vẫn nền sáng `#F8FAFC` để không "nặng mắt".
- **Badge trạng thái:** luôn dùng cặp màu nhạt/đậm ở bảng 7.2, không dùng màu đặc làm nền badge.
- **Card Job/Company:** nền trắng `#FFFFFF`, viền `#E2E8F0`, bo góc `12px`, tiêu đề `#0F172A`, mô tả phụ `#64748B`.

## 7.6. Cấu hình Tailwind (áp trực tiếp vào frontend)

```css
/* src/styles/globals.css — Tailwind CSS 4 */
@import "tailwindcss";

@theme {
  --font-sans: Inter, system-ui, sans-serif;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-accent: #10b981;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-status-draft-bg: #f1f5f9;
  --color-status-draft-text: #64748b;
  --color-status-pending-bg: #fef3c7;
  --color-status-pending-text: #b45309;
  --color-status-offer-bg: #ccfbf1;
  --color-status-offer-text: #0f766e;
  --color-status-hired-bg: #ecfdf5;
  --color-status-hired-text: #047857;
  --radius-card: 12px;
  --radius-modal: 16px;
}
```

---

# 8. Backlog P1/P2 — làm thêm nếu 5 tuần hoàn thành sớm

**P1 (rất nên có nếu dư thời gian):** Redis cache, export Excel, refresh token rotation, audit UI đầy đủ hơn.

**P2 (bonus, không bắt buộc):** 2FA, Google OAuth, Kanban kéo-thả, calendar UI, quét virus file CV (ClamAV), lưu file lên S3/MinIO thay vì local volume, gợi ý việc làm nâng cấp bằng `pgvector`, tính năng lưu job yêu thích, job alert qua email.

---

# 9. Definition of Done — MVP 5 tuần

Hệ thống được coi là **hoàn thành cơ bản** khi demo được liền mạch, không lỗi, kịch bản sau:

```text
1. Recruiter đăng nhập → tạo công ty → tạo job → submit.
2. Admin đăng nhập → xem job pending → duyệt → job Published.
3. Applicant đăng nhập → cập nhật hồ sơ + kỹ năng → upload CV.
4. Applicant tìm job theo từ khoá/kỹ năng → xem gợi ý AI mức độ phù hợp.
5. Applicant apply (chọn CV) → nhận notification xác nhận.
6. Recruiter xem pipeline → chuyển Applied → Screening → Interview.
7. Recruiter lên lịch phỏng vấn → applicant thấy lịch + notification.
8. Recruiter ghi kết quả phỏng vấn → tạo Offer.
9. Applicant xem Offer → Accept → trạng thái chuyển Hired.
10. Recruiter dashboard pipeline cập nhật đúng.
11. Admin xem báo cáo số tin/số ứng viên.
12. Recruiter dùng AI để soạn nhanh 1 JD.
```

---

# 10. Checklist bàn giao cuối (rút gọn cho 5 tuần)

**Business**
- [ ] 3 role hoạt động đúng, phân quyền theo resource (recruiter chỉ thấy job công ty mình).
- [ ] Job Draft → Pending → Published/Rejected.
- [ ] Search job theo từ khoá + kỹ năng.
- [ ] Hồ sơ ứng viên + upload nhiều CV, tải CV có kiểm tra quyền.
- [ ] Apply chặn trùng, có lịch sử trạng thái.
- [ ] Interview nhiều vòng, Offer có deadline + accept/reject.
- [ ] Notification khi đổi trạng thái quan trọng.
- [ ] Gợi ý việc làm + AI giải thích match + AI JD assistant.
- [ ] Dashboard pipeline theo role.
- [ ] Báo cáo số tin/số ứng viên (CSV).
- [ ] CV template PDF.

**Kỹ thuật (mức tối thiểu chấp nhận được)**
- [ ] JWT + refresh token, RBAC.
- [ ] Validate input, pagination/filter/sort ở các danh sách lớn.
- [ ] File CV lưu private, allowlist định dạng, giới hạn size.
- [ ] Swagger/OpenAPI.
- [ ] Vài unit/integration test cho luồng chính.
- [ ] Docker Compose chạy được toàn bộ hệ thống bằng 1 lệnh.
- [ ] Seed dữ liệu demo (200–300 record).
- [ ] README hướng dẫn cài đặt + tài khoản demo.

**Giao diện**
- [ ] Áp dụng đúng bảng màu ở mục 7 xuyên suốt toàn bộ giao diện.
- [ ] Badge trạng thái dùng đúng cặp màu nhạt/đậm quy định.
- [ ] Responsive cơ bản (desktop + tablet tối thiểu).
