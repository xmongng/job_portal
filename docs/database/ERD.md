# Cơ sở dữ liệu Job Portal MVP

Phiên bản 1.0 • 14/09/2026 • PostgreSQL 16 • Thiết kế để triển khai, chưa phải migration đã chạy.

Tài liệu này và [USE_CASES.md](../business-analysis/USE_CASES.md) là đặc tả nghiệp vụ/CSDL hiện hành. Nếu khác SRS, flow hoặc kế hoạch MVP cũ, dùng hai tài liệu này. Các quyết định dưới đây là baseline thiết kế của MVP, không mô tả nội bộ TopCV.

## 1. Phạm vi và quyết định

| Nội dung | Quyết định MVP |
|---|---|
| Vai trò | Một tài khoản có một role: APPLICANT, RECRUITER, ADMIN. Admin không đăng ký công khai. |
| Doanh nghiệp | Một recruiter thuộc tối đa một công ty đang tham gia; một công ty có nhiều recruiter, đúng một OWNER hoạt động. |
| Công ty | Duyệt hồ sơ thủ công; tách kết quả duyệt khỏi đình chỉ hoạt động. Không tự nhận quyền qua tên công ty/email domain. |
| Job | Một nhóm nghề, một địa điểm chính, nhiều kỹ năng; VND/tháng; có lương thỏa thuận. |
| CV | Upload PDF/DOC/DOCX hoặc tạo PDF từ một mẫu cố định. File đã tạo bất biến. |
| Ứng tuyển | Một application/applicant/job trong toàn bộ lịch sử, kể cả rút hoặc bị từ chối. |
| Pipeline | Cho phép bỏ screening riêng; bảng chuyển trạng thái ở mục 5 là danh sách cho phép duy nhất. |
| Offer | Nhiều lần phát hành nối tiếp; tối đa một DRAFT/SENT và một ACCEPTED/application. Accepted chưa tự thành Hired. |
| AI | Matching theo quy tắc; LLM giải thích matching và soạn JD. Không tự ra quyết định tuyển dụng. |
| Kênh thông báo | In-app bền vững trong DB; email có hàng đợi DB và retry đơn giản. |
| Ngoài phạm vi | Thanh toán, kho CV công khai, chat, CV editor kéo thả, phân quyền tùy biến, microservices. |

## 2. Sơ đồ quan hệ rút gọn

Chia theo nhóm để tránh đường nối chồng chéo. Bảng nối và khóa ngoại được mô tả đầy đủ trong từ điển dữ liệu.

```mermaid
erDiagram
  users ||--o{ company_memberships : participates
  companies ||--o{ company_memberships : contains
  companies ||--o{ jobs : owns
  users ||--o| applicants : profile
```

```mermaid
erDiagram
  applicants ||--o{ resumes : owns
  applicants ||--o{ applications : submits
  jobs ||--o{ applications : receives
  resumes ||--o{ applications : submitted_file
```

```mermaid
erDiagram
  applications ||--o{ application_status_history : records
  applications ||--o{ interviews : schedules
  applications ||--o{ offers : issues
  users ||--o{ notifications : receives
```

## 3. Quy ước dữ liệu

- PK mặc định: `id uuid`, sinh phía server. Bảng nối ghi rõ khóa ghép.
- Các bảng có PK id mặc định có `created_at timestamptz NOT NULL DEFAULT now()`. Bảng mutable có thêm `updated_at`; bảng append-only không có updated_at.
- Mọi cột trong bảng dưới là NOT NULL trừ khi có dấu `?`. Cột ? cho phép NULL. Giá trị mặc định được ghi trong mô tả; các giá trị còn lại phải được cung cấp.
- `FK → bảng.cột` mặc định ON DELETE RESTRICT. Không cascade xóa nghiệp vụ.
- Email: trim + lowercase trước lưu, unique trên giá trị chuẩn hóa. Không tự sửa dấu chấm hoặc dấu cộng.
- Thời gian lưu UTC, API dùng ISO 8601 có offset; giao diện chuyển múi giờ. Deadline là thời điểm chính xác, hết hạn khi now >= deadline.
- Tiền dùng numeric(14,2), không dùng float. Mã trạng thái dùng varchar + CHECK, không dùng PostgreSQL ENUM để dễ migration.
- Trường văn bản có giới hạn độ dài phía API. Nội dung JD/cover letter/feedback là plain text; không nhận HTML tùy ý.
- JSONB chỉ dùng cho dữ liệu snapshot/template/output AI có schema validation; không thay các quan hệ chính bằng JSON.
- Token bí mật chỉ lưu SHA-256 digest của token ngẫu nhiên đủ mạnh; mật khẩu dùng Argon2id. Không lưu token thô trong DB/log.
- Audit/history append-only với quyền DB phù hợp. Không áp dụng soft-delete đại trà: catalog ngừng sử dụng, nghiệp vụ kết thúc trạng thái, file có deleted_at.

## 4. Từ điển 29 bảng

### 4.1. users — tài khoản

- **Đại diện cho**: Con người cụ thể đăng ký và đăng nhập vào hệ thống (Ứng viên, Nhà tuyển dụng hoặc Quản trị viên).
- **Tại sao cần**: Quản lý thông tin xác thực, phân quyền và trạng thái bảo mật tập trung cho mọi tác nhân, tách biệt hoàn toàn khỏi hồ sơ chuyên môn cá nhân hay thông tin doanh nghiệp.
- **Các trường quan trọng & lý do**:
  - `email`: Định danh đăng nhập duy nhất, chuẩn hóa chữ thường để tránh trùng lặp tài khoản.
  - `password_hash`: Băm mật khẩu bằng Argon2id chống tấn công dò mật khẩu tốc độ cao.
  - `role`: Phân quyền chính (`APPLICANT`, `RECRUITER`, `ADMIN`), một người dùng chỉ giữ 1 vai trò duy nhất trong MVP.
  - `status` & `suspended_reason`: Cho phép đình chỉ (`SUSPENDED`) hoặc vô hiệu hóa tài khoản và bắt buộc lưu lý do giải trình.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Tài khoản |
| email | varchar(254) UNIQUE | Email chuẩn hóa |
| password_hash | text | Argon2id |
| role | varchar(16) | APPLICANT / RECRUITER / ADMIN |
| full_name | varchar(150) | Tên hiện tại |
| phone | varchar(32)? | Liên hệ |
| status | varchar(16) | ACTIVE / SUSPENDED / DEACTIVATED; mặc định ACTIVE |
| email_verified_at | timestamptz? | NULL khi chưa xác thực |
| suspended_reason | text? | Bắt buộc khi SUSPENDED |
| last_login_at | timestamptz? | Đăng nhập gần nhất |

Mutable. Không có API đổi role trong MVP. Quyền nhạy cảm kiểm tra trạng thái tài khoản hiện tại, không chỉ claim JWT cũ.

### 4.2. auth_sessions — phiên đăng nhập

- **Đại diện cho**: Một lần người dùng đăng nhập trên một thiết bị/trình duyệt cụ thể.
- **Tại sao cần**: Nếu chỉ dùng JWT đơn thuần thì khi đổi mật khẩu hoặc bị hack tài khoản, hệ thống không thể thu hồi quyền ngay lập tức. Bảng này lưu phiên phía server để có thể thu hồi (`revoke`) quyền truy cập tức thì.
- **Các trường quan trọng & lý do**:
  - `refresh_token_hash`: Lưu bản mã băm SHA-256 của refresh token (nếu lộ DB, kẻ tấn công cũng không dùng được token để chiếm phiên).
  - `revoked_at`: Đánh dấu thời điểm phiên bị hủy (khi đăng xuất, đổi mật khẩu, hoặc tài khoản bị Admin khóa).
  - `expires_at`: Hạn sử dụng tuyệt đối của phiên đăng nhập.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | session_id trong access token |
| user_id | uuid FK → users.id | Chủ phiên |
| refresh_token_hash | char(64) UNIQUE | Digest token hiện tại |
| expires_at | timestamptz | Hết hạn tuyệt đối |
| revoked_at | timestamptz? | Thu hồi |
| last_used_at | timestamptz? | Refresh gần nhất |

Mutable. Refresh xoay token trong transaction. Logout/đổi mật khẩu/khóa user thu hồi phiên theo use case. Access token ngắn hạn; API kiểm tra phiên chưa thu hồi.

### 4.3. account_tokens — xác thực email/đặt lại mật khẩu

- **Đại diện cho**: Mã token tạm thời phục vụ kích hoạt tài khoản hoặc đặt lại mật khẩu gửi qua email.
- **Tại sao cần**: Tách biệt luồng xác thực một lần ra khỏi bảng `users`, tránh phình dữ liệu và dễ dàng quản lý hạn sử dụng của từng loại mã xác thực.
- **Các trường quan trọng & lý do**:
  - `purpose`: Phân biệt mục đích sử dụng (`VERIFY_EMAIL` hoặc `RESET_PASSWORD`) để ngăn việc dùng token xác thực email đi đổi mật khẩu.
  - `token_hash`: Lưu digest SHA-256 của chuỗi token ngẫu nhiên để bảo mật.
  - `consumed_at`: Đảm bảo token chỉ được sử dụng đúng 1 lần duy nhất; phát token mới sẽ vô hiệu hóa token cũ cùng mục đích.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Token record |
| user_id | uuid FK → users.id | Chủ token |
| purpose | varchar(24) | VERIFY_EMAIL / RESET_PASSWORD |
| token_hash | char(64) UNIQUE | Digest |
| expires_at | timestamptz | Hạn sử dụng |
| consumed_at | timestamptz? | Dùng một lần |

Mutable. Phát token mới vô hiệu token cũ cùng purpose bằng consumed_at. Khóa bản ghi khi sử dụng.

### 4.4. companies — công ty

- **Đại diện cho**: Pháp nhân doanh nghiệp tuyển dụng trên nền tảng.
- **Tại sao cần**: Một công ty có thương hiệu, mã số thuế và quy chế hoạt động riêng, độc lập với các cá nhân nhân sự làm việc tại đó.
- **Các trường quan trọng & lý do**:
  - `registration_number`: Mã số thuế / Đăng ký kinh doanh duy nhất để Admin thẩm định pháp lý và phòng chống công ty mạo danh.
  - `verification_status` & `verification_note`: Trạng thái xét duyệt thủ công của Admin (`PENDING`, `VERIFIED`, `REJECTED`), bắt buộc ghi chú lý do khi từ chối.
  - `status` & `suspension_reason`: Quản lý tình trạng hoạt động (`ACTIVE`, `SUSPENDED`), tách rời khỏi kết quả duyệt ban đầu.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Công ty |
| name | varchar(200) | Tên doanh nghiệp |
| registration_number | varchar(32) UNIQUE | Mã đăng ký/mã số thuế; chuẩn hóa khoảng trắng |
| description | text | Giới thiệu |
| industry | varchar(120) | Lĩnh vực công ty, không phải nhóm nghề của job |
| size_band | varchar(16) | 1_10 / 11_50 / 51_200 / 201_500 / 501_1000 / ABOVE_1000 |
| website_url | varchar(2048)? | Chỉ HTTP(S), không fetch từ backend |
| logo_key | text? | Khóa ảnh đã kiểm tra; không chứa đường dẫn do client chọn |
| address | varchar(500) | Địa chỉ |
| location_id | uuid FK → locations.id | Tỉnh/thành |
| verification_status | varchar(16) | PENDING / VERIFIED / REJECTED |
| verification_note | text? | Bắt buộc khi REJECTED |
| reviewed_by | uuid? FK → users.id | Admin duyệt |
| reviewed_at | timestamptz? | Thời điểm duyệt |
| status | varchar(16) | ACTIVE / SUSPENDED |
| suspension_reason | text? | Bắt buộc khi SUSPENDED |
| created_by | uuid FK → users.id | Người khởi tạo |

Mutable. Hồ sơ mới PENDING/ACTIVE. Mã đăng ký duy nhất không chứng minh quyền sở hữu; admin duyệt thủ công theo checklist liên hệ/website/mã đăng ký. Đây là xét duyệt của nền tảng, không phải chứng nhận pháp lý. MVP khóa sửa name/registration_number sau VERIFIED; yêu cầu thay đổi qua admin ngoài luồng tự phục vụ.

### 4.5. company_memberships — thành viên tuyển dụng

- **Đại diện cho**: Mối quan hệ liên kết giữa một Nhà tuyển dụng (`RECRUITER`) và một Công ty cụ thể.
- **Tại sao cần**: Quản lý việc nhân sự gia nhập hoặc rời khỏi công ty; một công ty có thể có nhiều recruiter nhưng mỗi công ty luôn có đúng 1 OWNER hoạt động.
- **Các trường quan trọng & lý do**:
  - `membership_role`: Phân cấp vai trò (`OWNER` hoặc `MEMBER`), xác định quyền quản trị công ty và mời thành viên.
  - `left_at`: Đánh dấu ngày nhân sự rời công ty thay vì xóa cứng dòng dữ liệu, nhằm bảo toàn lịch sử các tin tuyển dụng và vòng phỏng vấn họ từng phụ trách.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Membership |
| company_id | uuid FK → companies.id | Công ty |
| user_id | uuid FK → users.id | Phải là RECRUITER |
| membership_role | varchar(8) | OWNER / MEMBER |
| joined_at | timestamptz | Ngày tham gia |
| left_at | timestamptz? | NULL là còn tham gia |

Mutable. Unique partial(user_id) WHERE left_at IS NULL. Unique partial(company_id) WHERE membership_role='OWNER' AND left_at IS NULL. Tạo công ty và OWNER cùng transaction. Không cho xóa/chuyển OWNER trong MVP; admin không khóa OWNER cuối cùng khi còn vận hành công ty mà chưa đình chỉ công ty.

### 4.6. company_invitations — lời mời thành viên

- **Đại diện cho**: Thư mời tham gia phòng tuyển dụng do `OWNER` công ty gửi tới email của nhân sự mới.
- **Tại sao cần**: Đảm bảo nhân sự không thể tự nhận mình thuộc công ty; họ bắt buộc phải nhận được lời mời chính thức từ chủ sở hữu.
- **Các trường quan trọng & lý do**:
  - `email`: Địa chỉ nhận thư mời, chuẩn hóa để chống trùng lặp.
  - `token_hash`: Chuỗi digest bảo mật đính kèm trong link kích hoạt mời.
  - `expires_at`: Lời mời hết hạn sau 7 ngày kể từ khi tạo.
  - `status`: Quản lý trạng thái (`PENDING`, `ACCEPTED`, `REVOKED`, `EXPIRED`).

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Lời mời |
| company_id | uuid FK → companies.id | Công ty |
| email | varchar(254) | Email nhận đã chuẩn hóa |
| invited_by | uuid FK → users.id | OWNER |
| token_hash | char(64) UNIQUE | Digest bí mật |
| status | varchar(16) | PENDING / ACCEPTED / REVOKED / EXPIRED |
| expires_at | timestamptz | 7 ngày kể từ tạo |
| accepted_by | uuid? FK → users.id | Người nhận |
| accepted_at | timestamptz? | Cùng có/không với accepted_by |

Mutable. Unique partial(company_id,email) WHERE status='PENDING'. Trước gửi lại, chuyển lời mời quá hạn sang EXPIRED trong transaction. Lời mời chỉ cấp MEMBER.

### 4.7. locations — danh mục tỉnh/thành

- **Đại diện cho**: Danh mục địa giới hành chính chuẩn hóa (Tỉnh/Thành phố tại Việt Nam).
- **Tại sao cần**: Thống nhất địa điểm làm việc và nơi sinh sống của ứng viên/công ty, giúp bộ lọc tìm kiếm và thuật toán gợi ý việc làm hoạt động chính xác.
- **Các trường quan trọng & lý do**:
  - `code`: Mã định danh ổn định của tỉnh/thành theo nguồn chuẩn.
  - `is_active`: Cho phép tắt kích hoạt địa điểm khi cần mà không phải xóa bản ghi đang được tham chiếu.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | ID ổn định |
| code | varchar(20) UNIQUE | Mã nguồn danh mục |
| name | varchar(150) | Tên hiển thị |
| is_active | boolean | Mặc định true |

Mutable. Seed theo một phiên bản danh mục có ngày nguồn; không xóa nơi đã được tham chiếu. Không xử lý ánh xạ lịch sử địa giới trong MVP.

### 4.8. job_categories — nhóm nghề

- **Đại diện cho**: Danh mục các lĩnh vực/ngành nghề tuyển dụng (ví dụ: CNTT, Marketing, Kế toán).
- **Tại sao cần**: Phân loại tin tuyển dụng để ứng viên tìm kiếm theo ngành nghề chuyên môn và phục vụ thống kê thị trường.
- **Các trường quan trọng & lý do**:
  - `name`: Tên nhóm nghề duy nhất.
  - `is_active`: Kiểm soát việc bật/tắt nhóm nghề trong danh mục phẳng của MVP.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Nhóm nghề |
| name | varchar(120) UNIQUE | Tên |
| is_active | boolean | Mặc định true |

Mutable. Danh mục phẳng, seed/admin quản lý; không phân cấp nhiều tầng.

### 4.9. skills — kỹ năng chuẩn hóa

- **Đại diện cho**: Danh mục các kỹ năng chuyên môn được hệ thống công nhận (ví dụ: Python, Docker, Figma).
- **Tại sao cần**: Tránh tình trạng người dùng nhập tùy tiện các biến thể tên khác nhau làm sai lệch kết quả lọc và chấm điểm phù hợp của AI.
- **Các trường quan trọng & lý do**:
  - `normalized_name`: Tên kỹ năng đã trim và viết thường (ví dụ: `python`) có ràng buộc `UNIQUE` chống tạo trùng.
  - `is_active`: Quản lý việc ngừng sử dụng kỹ năng mà không làm hỏng dữ liệu liên kết cũ.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Kỹ năng |
| name | varchar(100) | Tên hiển thị |
| normalized_name | varchar(100) UNIQUE | Trim/lowercase; ví dụ python |
| is_active | boolean | Mặc định true |

Mutable. Không tự tạo skill từ text AI hoặc tag do client gửi.

### 4.10. applicants — hồ sơ ứng viên

- **Đại diện cho**: Hồ sơ năng lực và nguyện vọng tìm việc của ứng viên trên nền tảng.
- **Tại sao cần**: Lưu trữ thông tin nghề nghiệp tổng quát phục vụ tìm kiếm việc làm và tính toán độ phù hợp (matching), tách biệt với tài khoản đăng nhập.
- **Các trường quan trọng & lý do**:
  - `desired_salary_min` & `desired_salary_max`: Khoảng lương mong muốn (VND/tháng) để so khớp với mức lương tin tuyển dụng.
  - `preferred_work_mode`: Nguyện vọng hình thức làm việc (`ONSITE`, `HYBRID`, `REMOTE`).
  - `years_experience`: Tổng số năm kinh nghiệm thực tế.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Hồ sơ |
| user_id | uuid UNIQUE FK → users.id | Phải là APPLICANT |
| headline | varchar(200)? | Chức danh mong muốn |
| summary | text? | Giới thiệu |
| location_id | uuid? FK → locations.id | Nơi sinh sống |
| preferred_location_id | uuid? FK → locations.id | Địa điểm muốn làm |
| years_experience | numeric(4,1)? | >= 0 |
| desired_salary_min | numeric(14,2)? | >= 0, VND/tháng |
| desired_salary_max | numeric(14,2)? | >= min nếu cả hai có giá trị |
| preferred_work_mode | varchar(8)? | ONSITE / HYBRID / REMOTE |
| preferred_employment_type | varchar(16)? | FULL_TIME / PART_TIME / INTERNSHIP / CONTRACT |

Mutable. Hồ sơ tạo cùng tài khoản; không bắt buộc điền hết để tìm việc. Thiếu dữ liệu matching được xử lý theo UC-29.

### 4.11. applicant_educations — học vấn

- **Đại diện cho**: Lịch sử học tập, bằng cấp và cơ sở đào tạo của ứng viên.
- **Tại sao cần**: Một ứng viên có thể học nhiều trường hoặc nhiều chương trình đào tạo khác nhau (quan hệ 1-Nhiều).
- **Các trường quan trọng & lý do**:
  - `start_date` & `end_date`: Khoảng thời gian theo học; `end_date = NULL` thể hiện đang tiếp tục theo học.
  - `institution` & `degree`: Tên trường đào tạo và bậc học/văn bằng đạt được.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Học vấn |
| applicant_id | uuid FK → applicants.id | Chủ |
| institution | varchar(200) | Trường |
| degree | varchar(100)? | Bằng cấp |
| field_of_study | varchar(150)? | Ngành |
| start_date | date | Bắt đầu |
| end_date | date? | NULL nếu đang học |
| description | text? | Bổ sung |

Mutable. end_date >= start_date; không khai báo ngày bắt đầu trong tương lai.

### 4.12. applicant_experiences — kinh nghiệm

- **Đại diện cho**: Quá trình làm việc thực tế của ứng viên tại các công ty trước đây.
- **Tại sao cần**: Cung cấp bức tranh toàn diện về lộ trình nghề nghiệp cho nhà tuyển dụng đánh giá.
- **Các trường quan trọng & lý do**:
  - `company_name`: Tên công ty do ứng viên tự khai báo (không tạo khóa ngoại sang bảng `companies`).
  - `start_date` & `end_date`: Khoảng thời gian công tác; `end_date = NULL` thể hiện vị trí công việc hiện tại. Cho phép các giai đoạn chồng nhau để hỗ trợ làm song song nhiều công việc.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Kinh nghiệm |
| applicant_id | uuid FK → applicants.id | Chủ |
| company_name | varchar(200) | Tên tự khai, không FK companies |
| job_title | varchar(200) | Vị trí |
| start_date | date | Bắt đầu |
| end_date | date? | NULL nếu đang làm |
| description | text? | Công việc/kết quả |

Mutable. end_date >= start_date. Cho phép các giai đoạn chồng nhau để hỗ trợ làm song song.

### 4.13. applicant_skills — kỹ năng hồ sơ

- **Đại diện cho**: Bảng liên kết giữa Ứng viên và Danh mục kỹ năng chuẩn hóa (quan hệ Nhiều-Nhiều).
- **Tại sao cần**: Gắn các kỹ năng ứng viên sở hữu vào hồ sơ để hệ thống và AI thực hiện so khớp với yêu cầu của tin tuyển dụng.
- **Các trường quan trọng & lý do**:
  - Khóa chính ghép `(applicant_id, skill_id)`: Đảm bảo không gắn trùng lặp một kỹ năng vào một hồ sơ; giới hạn tối đa 50 kỹ năng/hồ sơ.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| applicant_id | uuid FK → applicants.id | PK ghép |
| skill_id | uuid FK → skills.id | PK ghép |

Không có id/timestamp mặc định. PK(applicant_id,skill_id). Tối đa 50 skill/hồ sơ; xóa liên kết không xóa danh mục.

### 4.14. cv_documents — nội dung CV theo mẫu

- **Đại diện cho**: Bản soạn thảo CV trực tuyến do ứng viên xây dựng bằng công cụ tạo CV (CV Builder) trên website.
- **Tại sao cần**: Cho phép ứng viên lưu trữ, chỉnh sửa linh hoạt và chọn mẫu giao diện để xuất ra file PDF hoàn chỉnh.
- **Các trường quan trọng & lý do**:
  - `content (jsonb)`: Lưu toàn bộ cấu trúc CV theo schema chuẩn (`contact`, `summary`, `education`, `experience`, `skills`, `projects`), đã được validate chặt chẽ.
  - `revision`: Số phiên bản tăng dần mỗi lần chỉnh sửa, dùng để truy vết khi xuất bản file.
  - `template_code`: Mã mẫu giao diện áp dụng (MVP sử dụng mẫu cố định `BASIC_V1`).

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Bản soạn CV |
| applicant_id | uuid FK → applicants.id | Chủ |
| title | varchar(150) | Tên bản soạn |
| template_code | varchar(32) | MVP: BASIC_V1 |
| content | jsonb | Schema CV_V1 |
| revision | integer | >=1, tăng khi sửa |
| deleted_at | timestamptz? | Xóa mềm |

Mutable. content chứa contact{name,email,phone}, summary, education[], experience[], skills[], projects[]. Validate kiểu/độ dài; không nhận HTML, script, URL tải ảnh/font. Khởi tạo có thể sao chép hồ sơ; sửa CV không sửa ngược hồ sơ.

### 4.15. resumes — file CV bất biến

- **Đại diện cho**: File tài liệu CV thực tế (PDF, DOC, DOCX) sẵn sàng dùng để nộp đơn ứng tuyển.
- **Tại sao cần**: Là tài liệu pháp lý khi tuyển dụng. File CV mang tính **bất biến (immutable)**; khi nộp đơn, nhà tuyển dụng phải luôn xem đúng bản CV tại thời điểm đó kể cả ứng viên có chỉnh sửa hồ sơ sau này.
- **Các trường quan trọng & lý do**:
  - `source`: Nguồn gốc CV (`UPLOAD` từ máy tính hoặc `GENERATED` từ bản soạn thảo `cv_documents`).
  - `storage_key`: Đường dẫn file trên hạ tầng lưu trữ riêng tư (private storage).
  - `sha256`: Mã băm kiểm tra tính toàn vẹn của tệp tin.
  - `is_default`: Đánh dấu CV mặc định để nộp nhanh.
  - `deleted_at`: Xóa mềm để ẩn khỏi danh sách lựa chọn của ứng viên nhưng vẫn bảo toàn file nếu đã có đơn ứng tuyển tham chiếu.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | File |
| applicant_id | uuid FK → applicants.id | Chủ |
| source | varchar(16) | UPLOAD / GENERATED |
| cv_document_id | uuid? FK → cv_documents.id | Bắt buộc khi GENERATED |
| document_revision | integer? | Revision lúc xuất |
| title | varchar(150) | Tên hiển thị, được sửa |
| storage_key | text UNIQUE | Khóa file private |
| original_name | varchar(255) | Tên tải xuống đã làm sạch |
| mime_type | varchar(100) | Allowlist |
| size_bytes | bigint | >0 và <=5 MiB |
| sha256 | char(64) | Kiểm tra tính toàn vẹn, không unique toàn hệ thống |
| is_default | boolean | Mặc định false |
| deleted_at | timestamptz? | Ẩn khỏi danh sách chọn |

Mutable chỉ title/is_default/deleted_at. File và source metadata bất biến. CHECK source/generated fields nhất quán. Unique partial(applicant_id) WHERE is_default AND deleted_at IS NULL; CHECK deleted_at IS NULL OR NOT is_default. CV ẩn nhưng đã nộp vẫn tải được qua quyền application trong thời hạn lưu dữ liệu.

### 4.16. jobs — tin tuyển dụng

- **Đại diện cho**: Một vị trí công việc cụ thể mà doanh nghiệp cần tuyển nhân sự.
- **Tại sao cần**: Là trung tâm hoạt động kinh doanh của sàn tuyển dụng, kết nối nhu cầu tìm việc và tuyển dụng.
- **Các trường quan trọng & lý do**:
  - `status`: Quản lý vòng đời chặt chẽ (`DRAFT`, `PENDING_APPROVAL`, `REJECTED`, `PUBLISHED`, `CLOSED`). Tin đăng chỉ xuất bản ra công chúng khi được Admin duyệt.
  - `salary_min`, `salary_max`, `is_negotiable`: Minh bạch hóa mức lương. Nếu `is_negotiable = true` thì hai mức lương để trống; ngược lại bắt buộc có khoảng lương cụ thể tính theo VND/tháng.
  - `deadline`: Hạn nộp hồ sơ, hết hạn hệ thống sẽ tự động đóng tin.
  - `version`: Khóa lạc quan (Optimistic Locking) chống lỗi ghi đè dữ liệu khi nhiều người cùng thao tác.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Job |
| company_id | uuid FK → companies.id | Công ty |
| created_by | uuid FK → users.id | Recruiter tạo |
| title | varchar(200) | Tiêu đề |
| description | text? | Mô tả |
| requirements | text? | Yêu cầu |
| benefits | text? | Quyền lợi |
| category_id | uuid? FK → job_categories.id | Nhóm nghề |
| location_id | uuid? FK → locations.id | Địa điểm chính |
| address | varchar(500)? | Địa chỉ |
| employment_type | varchar(16)? | Như applicants |
| work_mode | varchar(8)? | Như applicants |
| seniority | varchar(16)? | INTERN / JUNIOR / MIDDLE / SENIOR / LEAD / MANAGER |
| experience_min_years | numeric(4,1)? | >=0 |
| vacancy_count | integer? | >0; số lượng dự kiến, không tự đóng khi đủ |
| salary_min | numeric(14,2)? | >=0 |
| salary_max | numeric(14,2)? | >= min |
| is_negotiable | boolean | Mặc định true |
| currency | char(3) | CHECK='VND', mặc định VND |
| salary_period | varchar(8) | CHECK='MONTH', mặc định MONTH |
| deadline | timestamptz? | Bắt buộc khi submit |
| status | varchar(24) | DRAFT / PENDING_APPROVAL / REJECTED / PUBLISHED / CLOSED |
| published_at | timestamptz? | Lần duyệt thành công |
| closed_at | timestamptz? | Đóng |
| closure_reason | text? | Lý do |
| version | integer | >=1; chống ghi đè khi sửa/chuyển trạng thái |

Mutable có kiểm soát. Draft cho phép thiếu trường. Khi submit bắt buộc description/requirements/benefits/category/employment/work_mode/seniority/experience/vacancy/deadline; onsite/hybrid cần location/address. Nếu negotiable=true thì hai salary NULL; ngược lại cả hai bắt buộc, max>=min. Áp CHECK lương và số không âm cả ở draft; required theo trạng thái được validation/constraint tương ứng. PUBLISHED không sửa nội dung, chỉ đóng; sao chép tạo job DRAFT mới.

### 4.17. job_skills — yêu cầu kỹ năng

- **Đại diện cho**: Danh sách các kỹ năng chuẩn hóa mà công việc yêu cầu ứng viên cần có (quan hệ Nhiều-Nhiều giữa Jobs và Skills).
- **Tại sao cần**: Đóng vai trò làm tiêu chí chính để bộ lọc tìm kiếm và thuật toán AI tính toán độ phù hợp (matching score) giữa ứng viên và công việc.
- **Các trường quan trọng & lý do**:
  - Khóa chính ghép `(job_id, skill_id)`: Ràng buộc mỗi kỹ năng chỉ gắn một lần vào tin tuyển dụng; khi gửi duyệt bắt buộc có từ 1 đến 30 kỹ năng.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| job_id | uuid FK → jobs.id | PK ghép |
| skill_id | uuid FK → skills.id | PK ghép |

PK(job_id,skill_id), không id/timestamp. Submit yêu cầu 1–30 skill active. Là tiêu chí matching, không phải cổng tự loại ứng viên.

### 4.18. job_status_history — lịch sử tin

- **Đại diện cho**: Nhật ký kiểm toán mọi sự kiện chuyển đổi trạng thái của tin tuyển dụng.
- **Tại sao cần**: Minh bạch hóa quy trình vận hành và kiểm duyệt, giúp giải trình khi tin bị từ chối hoặc bị đóng bất thường.
- **Các trường quan trọng & lý do**:
  - `from_status` & `to_status`: Ghi nhận trạng thái nguồn và trạng thái đích.
  - `changed_by` & `actor_type`: Người thực hiện thay đổi (`USER` hoặc `SYSTEM`).
  - `reason`: Bắt buộc nhập lý do khi Admin từ chối phê duyệt hoặc khi đóng tin tuyển dụng.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Sự kiện |
| job_id | uuid FK → jobs.id | Job |
| from_status | varchar(24)? | NULL lần tạo |
| to_status | varchar(24) | Trạng thái đích |
| changed_by | uuid? FK → users.id | NULL nếu system |
| reason | text? | Bắt buộc reject/close |
| actor_type | varchar(8) | USER / SYSTEM |

Append-only. created_at là thời điểm đổi. Đồng transaction với jobs; lưu từ NULL đến DRAFT khi tạo.

### 4.19. applications — đơn ứng tuyển

- **Đại diện cho**: Hồ sơ ứng tuyển của một ứng viên vào một tin tuyển dụng cụ thể.
- **Tại sao cần**: Là thực thể điều phối trung tâm của toàn bộ hệ thống quản lý ứng viên (Applicant Tracking System - ATS).
- **Các trường quan trọng & lý do**:
  - `UNIQUE(applicant_id, job_id)`: Chặn spam — 1 ứng viên chỉ được nộp đúng 1 đơn cho 1 công việc trong suốt lịch sử.
  - `contact_name, contact_email, contact_phone`: **Snapshot thông tin liên hệ** tại thời điểm nộp, không bị ảnh hưởng nếu ứng viên sửa thông tin cá nhân sau này.
  - `resume_id`: Liên kết trực tiếp tới file CV đã chọn khi nộp.
  - `status`: Quản lý tiến trình xử lý qua pipeline (`APPLIED`, `SCREENING`, `INTERVIEW`, `OFFER`, `HIRED`, `REJECTED`, `WITHDRAWN`).
  - `version`: Khóa lạc quan chống tranh chấp khi ứng viên và recruiter cùng thao tác đồng thời.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Đơn |
| job_id | uuid FK → jobs.id | Job |
| applicant_id | uuid FK → applicants.id | Người nộp |
| resume_id | uuid FK → resumes.id | File đã chọn |
| contact_name | varchar(150) | Snapshot khi nộp |
| contact_email | varchar(254) | Snapshot, từ email tài khoản đã xác thực |
| contact_phone | varchar(32) | Snapshot |
| cover_letter | text? | <=3000 ký tự |
| status | varchar(16) | APPLIED / SCREENING / INTERVIEW / OFFER / HIRED / REJECTED / WITHDRAWN |
| version | integer | >=1 |
| ended_at | timestamptz? | Có khi HIRED/REJECTED/WITHDRAWN |

Mutable chỉ trạng thái/version/ended_at. created_at là applied_at, không nhân đôi. UNIQUE(applicant_id,job_id). UNIQUE(resumes.id,applicant_id) trên resumes và composite FK applications(resume_id,applicant_id) → resumes(id,applicant_id) để chặn CV khác chủ ở DB. Snapshot chỉ bất biến đến khi có quy trình xóa/ẩn danh dữ liệu hợp lệ.

### 4.20. application_status_history — lịch sử đơn

- **Đại diện cho**: Nhật ký từng bước di chuyển của đơn ứng tuyển trong quy trình tuyển dụng.
- **Tại sao cần**: Cung cấp bức tranh toàn cảnh để ứng viên theo dõi lộ trình hồ sơ, đồng thời giúp doanh nghiệp đo lường hiệu suất tuyển dụng.
- **Các trường quan trọng & lý do**:
  - `from_status` & `to_status`: Truy vết các mốc thay đổi trạng thái trong pipeline.
  - `changed_by`: Ghi nhận danh tính người chuyển trạng thái (Recruiter, Applicant hoặc Hệ thống).
  - `reason`: Lý do bắt buộc khi từ chối hồ sơ (`REJECTED`), ứng viên rút đơn (`WITHDRAWN`), hoặc chuyển ngược lại phỏng vấn để thương lượng lại offer.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Sự kiện |
| application_id | uuid FK → applications.id | Đơn |
| from_status | varchar(16)? | NULL lúc nộp |
| to_status | varchar(16) | Đích |
| changed_by | uuid? FK → users.id | Người thực hiện |
| actor_type | varchar(8) | USER / SYSTEM |
| reason | text? | Bắt buộc reject, withdraw, quay lại interview |

Append-only. Không lưu feedback nội bộ vào reason công khai. Applicant xem lịch sử công khai qua DTO riêng.

### 4.21. application_notes — ghi chú nội bộ

- **Đại diện cho**: Các nhận xét, đánh giá riêng tư giữa các Recruiter trong cùng công ty về một hồ sơ ứng viên.
- **Tại sao cần**: Tạo không gian trao đổi nội bộ cho đội ngũ tuyển dụng mà **ứng viên tuyệt đối không thể nhìn thấy**.
- **Các trường quan trọng & lý do**:
  - `author_id`: Danh tính recruiter tạo ghi chú.
  - `content`: Nội dung nhận xét chi tiết (chế độ append-only, ghi chú tiếp theo để đính chính thay vì sửa bản ghi cũ).

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Ghi chú |
| application_id | uuid FK → applications.id | Đơn |
| author_id | uuid FK → users.id | Recruiter cùng công ty |
| content | text | 1–3000 ký tự |

Append-only trong MVP; sửa sai bằng ghi chú tiếp theo. Không trả applicant hoặc public.

### 4.22. interviews — các vòng phỏng vấn

- **Đại diện cho**: Lịch hẹn một buổi phỏng vấn cụ thể giữa doanh nghiệp và ứng viên (Vòng 1, Vòng 2, v.v.).
- **Tại sao cần**: Lên lịch, quản lý thời gian, hình thức và lưu kết quả đánh giá vòng phỏng vấn.
- **Các trường quan trọng & lý do**:
  - `round_number`: Thứ tự vòng phỏng vấn (1, 2, ...), không cho phép trùng số vòng trong cùng một đơn.
  - `mode` (`ONLINE` / `OFFLINE`): Bắt buộc có `meeting_url` nếu Online hoặc có `address` nếu Offline.
  - `status` (`SCHEDULED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`): Quản lý trạng thái buổi phỏng vấn.
  - `result` (`PASS`, `FAIL`, `UNDECIDED`): Kết quả đánh giá chỉ được cập nhật sau khi buổi phỏng vấn đã hoàn tất.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Vòng |
| application_id | uuid FK → applications.id | Đơn |
| round_number | integer | >0; UNIQUE(application_id,round_number) |
| starts_at | timestamptz | Bắt đầu |
| ends_at | timestamptz | > starts_at |
| mode | varchar(8) | ONLINE / OFFLINE |
| meeting_url | varchar(2048)? | HTTP(S), bắt buộc online |
| address | varchar(500)? | Bắt buộc offline |
| interviewer_name | varchar(150) | Không cần module lịch nhân sự |
| status | varchar(16) | SCHEDULED / COMPLETED / CANCELLED / NO_SHOW |
| result | varchar(16)? | PASS / FAIL / UNDECIDED; chỉ khi COMPLETED |
| feedback | text? | Nội bộ <=5000 ký tự |
| cancellation_reason | text? | Bắt buộc CANCELLED |
| created_by | uuid FK → users.id | Recruiter |
| version | integer | >=1 |

Mutable. Không tái sử dụng số vòng bị hủy. MVP chặn trùng lịch SCHEDULED của cùng application; không quản lý lịch interviewer giữa các công ty. Khóa application khi kiểm tra khoảng giờ giao nhau.

### 4.23. offers — các lần phát hành offer

- **Đại diện cho**: Lời mời nhận việc và các điều kiện đãi ngộ chính thức mà doanh nghiệp gửi tới ứng viên.
- **Tại sao cần**: Pháp lý hóa bước thỏa thuận lao động, cho phép ứng viên xác nhận chấp thuận hoặc từ chối có lưu vết.
- **Các trường quan trọng & lý do**:
  - `sequence_number`: Hỗ trợ đàm phán nhiều lần nối tiếp (nếu offer lần 1 bị từ chối, recruiter có thể gửi offer lần 2 với đãi ngộ mới).
  - `salary`, `start_date`, `response_deadline`: Mức lương cụ thể (gross VND/tháng), ngày dự kiến nhận việc và hạn chót phản hồi.
  - `status`: Quản lý tiến trình (`DRAFT`, `SENT`, `ACCEPTED`, `REJECTED`, `WITHDRAWN`, `EXPIRED`).
  - Ràng buộc: Tối đa 1 offer ở trạng thái `DRAFT` hoặc `SENT`, và tối đa 1 offer `ACCEPTED` trên mỗi đơn ứng tuyển.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Offer |
| application_id | uuid FK → applications.id | Đơn |
| sequence_number | integer | >0; UNIQUE(application_id,sequence_number) |
| salary | numeric(14,2) | >0, VND/tháng, gross |
| currency | char(3) | CHECK='VND' |
| start_date | date | Ngày bắt đầu dự kiến |
| response_deadline | timestamptz | Hạn phản hồi |
| terms | text | Điều kiện 1–10000 ký tự |
| status | varchar(16) | DRAFT / SENT / ACCEPTED / REJECTED / WITHDRAWN / EXPIRED |
| created_by | uuid FK → users.id | Recruiter |
| sent_at | timestamptz? | Có từ lúc gửi |
| responded_at | timestamptz? | Có khi ACCEPTED/REJECTED |
| response_note | text? | Applicant nhập, <=1000 |
| withdrawn_at | timestamptz? | Có khi WITHDRAWN |
| withdrawal_reason | text? | Bắt buộc WITHDRAWN |
| version | integer | >=1 |

Mutable theo state. Unique partial(application_id) WHERE status IN ('DRAFT','SENT'); unique partial(application_id) WHERE status='ACCEPTED'. Sau SENT, không sửa salary/terms/deadline/start_date. Muốn thương lượng lại: thu hồi hoặc đợi kết quả, application trở về INTERVIEW, tạo offer mới. Offer ACCEPTED giữ nguyên khi application bị rút/từ chối sau đó, để bảo toàn sự kiện chấp nhận.

### 4.24. notifications — thông báo trong ứng dụng

- **Đại diện cho**: Hộp thư thông báo trực tiếp trên giao diện website (hình quả chuông in-app).
- **Tại sao cần**: Cập nhật tức thời cho người dùng về các biến động liên quan đến họ (lịch phỏng vấn mới, kết quả duyệt tin, nhận offer).
- **Các trường quan trọng & lý do**:
  - `event_key`: Khóa định danh sự kiện duy nhất, chống tạo trùng nhiều thông báo cho cùng một hành động.
  - `read_at`: Đánh dấu thời điểm người dùng đã bấm xem thông báo.
  - `resource_type` & `resource_id`: Điều hướng người dùng tới đối tượng liên quan khi click vào thông báo.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Thông báo |
| user_id | uuid FK → users.id | Người nhận |
| event_key | varchar(200) | Khóa sự kiện xác định |
| type | varchar(64) | Mã sự kiện |
| title | varchar(200) | Tiêu đề |
| body | text | Thông điệp không chứa CV/token/feedback nội bộ |
| resource_type | varchar(32)? | JOB / APPLICATION / INTERVIEW / OFFER / COMPANY |
| resource_id | uuid? | Tham chiếu điều hướng, không FK đa hình |
| read_at | timestamptz? | Chưa đọc nếu NULL |

Mutable read_at. UNIQUE(user_id,event_key). Bấm liên kết vẫn kiểm tra quyền ở API tài nguyên.

### 4.25. email_deliveries — hàng đợi email

- **Đại diện cho**: Hàng đợi các tác vụ gửi email nền (Background Queue).
- **Tại sao cần**: Gửi email qua SMTP có độ trễ lớn và rủi ro gián đoạn mạng. Bảng này giúp API phản hồi tức thì cho người dùng, trong khi tiến trình nền (Worker) chịu trách nhiệm gửi và tự động thử lại (retry) khi gặp lỗi.
- **Các trường quan trọng & lý do**:
  - `status`, `attempts`, `next_attempt_at`: Quản lý cơ chế retry thông minh (tối đa 5 lần theo chu kỳ dãn cách 1/5/15/60 phút).
  - `locked_until`: Khóa tạm thời (lease 2 phút) khi worker đang xử lý nhằm ngăn ngừa 2 worker cùng gửi một email.
  - `payload_ciphertext`: Nội dung email được mã hóa bảo mật trong database và tự động xóa sau 7 ngày gửi thành công.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Delivery |
| user_id | uuid? FK → users.id | NULL nếu mời email chưa có tài khoản |
| notification_id | uuid? FK → notifications.id | Nếu phát từ in-app |
| dedup_key | varchar(200) UNIQUE | Chống tạo tác vụ trùng |
| recipient | varchar(254) | Người nhận |
| template_code | varchar(64) | Template cho phép |
| payload_ciphertext | bytea | Payload mã hóa ứng dụng, gồm link token nếu cần |
| status | varchar(16) | PENDING / PROCESSING / SENT / FAILED |
| attempts | integer | >=0, mặc định 0 |
| next_attempt_at | timestamptz | Lịch retry |
| locked_until | timestamptz? | Lease để phục hồi worker chết |
| sent_at | timestamptz? | Hoàn thành |
| last_error_code | varchar(64)? | Mã lỗi an toàn, không raw response chứa bí mật |

Mutable. Khóa mã hóa nằm ngoài DB; payload bị xóa hoặc thay bằng payload rỗng mã hóa sau gửi/hết hạn retention. Worker dùng FOR UPDATE SKIP LOCKED, lease 2 phút; tối đa 5 lần, backoff 1/5/15/60 phút. Email là at-least-once, có thể trùng khi SMTP thành công nhưng worker chết trước commit; in-app không trùng.

### 4.26. audit_logs — sự kiện nhạy cảm

- **Đại diện cho**: Hộp đen an ninh ghi vết các thao tác có độ nhạy cảm cao hoặc tiềm ẩn rủi ro vi phạm dữ liệu.
- **Tại sao cần**: Phục vụ công tác thanh tra, bảo mật và truy cứu trách nhiệm pháp lý khi xảy ra sự cố.
- **Các trường quan trọng & lý do**:
  - `action`: Hành động nhạy cảm (`COMPANY_REVIEW`, `JOB_APPROVE`, `CV_DOWNLOAD_AUTHORIZED`, v.v.).
  - `actor_id` & `request_id`: Xác định ai thực hiện và mã request tương ứng.
  - `outcome`: Kết quả thực thi (`SUCCESS`, `DENIED`, `FAILURE`).
  - Bảng chỉ cho phép ghi mới (`append-only`), tuyệt đối không lưu dữ liệu nhạy cảm (mật khẩu, token thô, file CV) vào metadata.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Sự kiện |
| actor_id | uuid? FK → users.id | NULL nếu system |
| action | varchar(64) | COMPANY_REVIEW, JOB_APPROVE, CV_DOWNLOAD_AUTHORIZED… |
| entity_type | varchar(32) | Loại đối tượng |
| entity_id | uuid? | Tham chiếu, không FK đa hình |
| request_id | uuid | Liên kết request |
| outcome | varchar(16) | SUCCESS / DENIED / FAILURE |
| metadata | jsonb | Allowlist: status cũ/mới, reason_code; không CV/token/prompt |

Append-only. CV_DOWNLOAD_AUTHORIZED ghi trước cấp stream; không khẳng định client nhận xong file. Log từ chối ngoài transaction bị rollback của nghiệp vụ.

### 4.27. ai_operations — cache và theo dõi AI

- **Đại diện cho**: Nhật ký và bộ nhớ đệm (Cache) của các lần hệ thống gọi API mô hình ngôn ngữ lớn (LLM).
- **Tại sao cần**:
  1. Tiết kiệm chi phí: Cache kết quả trong 24 giờ để tránh gọi lại API bên ngoài cho cùng một nội dung phân tích.
  2. Đo lường chi phí: Ghi nhận số lượng token tiêu thụ để kiểm soát hóa đơn AI.
- **Các trường quan trọng & lý do**:
  - `feature`: Tính năng ứng dụng AI (`MATCH_EXPLANATION` giải thích độ phù hợp CV, hoặc `JD_DRAFT` gợi ý mô tả công việc).
  - `input_hash`: Mã băm nội dung đầu vào đã chuẩn hóa dùng để đối soát nhanh trong cache.
  - `input_tokens` & `output_tokens`: Số token tiêu thụ thực tế.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| id | uuid PK | Lần gọi |
| requested_by | uuid FK → users.id | Người dùng |
| feature | varchar(24) | MATCH_EXPLANATION / JD_DRAFT |
| applicant_id | uuid? FK → applicants.id | Matching |
| job_id | uuid? FK → jobs.id | Matching hoặc job nháp |
| input_hash | char(64) | Hash input đã tối thiểu hóa, có prompt/scoring version |
| provider | varchar(32) | Nhà cung cấp |
| model | varchar(100) | Model thực dùng |
| prompt_version | varchar(32) | Phiên bản |
| status | varchar(16) | SUCCEEDED / FAILED |
| output | jsonb? | Kết quả đã validate, tối thiểu dữ liệu cá nhân |
| error_code | varchar(64)? | Lỗi an toàn |
| input_tokens | integer? | >=0 |
| output_tokens | integer? | >=0 |
| expires_at | timestamptz | TTL cache mặc định 24h |

Append-only. Không lưu prompt thô/API key. Cache lookup theo requested_by,feature,input_hash,model,prompt_version và SUCCEEDED chưa hết hạn; không chia sẻ output riêng tư giữa user. Feature matching bắt buộc applicant/job; JD_DRAFT có thể chưa có job_id. Input hash dùng nội dung canonical, không chỉ ID.

### 4.28. ai_rate_windows — giới hạn AI dùng chung

- **Đại diện cho**: Hạn ngạch (Quota) tiêu thụ AI của từng người dùng theo từng ngày.
- **Tại sao cần**: Ngăn chặn người dùng spam tính năng AI gây cạn kiệt ngân sách hoặc làm nghẽn tài nguyên hệ thống.
- **Các trường quan trọng & lý do**:
  - Khóa chính ghép `(user_id, feature, window_start)`: Theo dõi lượt gọi của từng user cho từng tính năng theo chu kỳ ngày (đầu ngày UTC).
  - `request_count`: Số lượt đã gọi trong ngày (mặc định giới hạn tối đa 20 lần/user/tính năng/ngày).

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| user_id | uuid FK → users.id | PK ghép |
| feature | varchar(24) | PK ghép |
| window_start | timestamptz | PK ghép, đầu ngày UTC |
| request_count | integer | >=0 |
| reserved_tokens | integer | >=0 |

Không id/timestamp. Tăng atomically trước gọi provider, giới hạn cấu hình mặc định 20 lần/user/feature/ngày; cache hit không tính. Giới hạn concurrency/timeout ở dịch vụ. Xóa window cũ sau 7 ngày.

### 4.29. security_rate_windows — giới hạn endpoint nhạy cảm

- **Đại diện cho**: Hạn mức tần suất (Rate Limit) cho các cổng API nhạy cảm về bảo mật (Đăng nhập, Đăng ký, Đổi mật khẩu, Gửi lại xác thực).
- **Tại sao cần**: Phòng thủ chống lại các cuộc tấn công dò mật khẩu tự động (brute-force), tấn công từ chối dịch vụ (DoS) hoặc spam làm nghẽn dịch vụ gửi mail.
- **Các trường quan trọng & lý do**:
  - `scope`: Phạm vi áp dụng giới hạn (`LOGIN`, `REGISTER`, `RESET`, `VERIFY_RESEND`).
  - `subject_hash`: Mã băm HMAC của IP hoặc Email (bảo vệ quyền riêng tư người dùng trong log giới hạn).
  - `window_start` & `request_count`: Bộ đếm số lần yêu cầu trong cửa sổ 15 phút.

| Cột | Kiểu | Ý nghĩa/ràng buộc |
|---|---|---|
| scope | varchar(32) | PK ghép: LOGIN / REGISTER / RESET / VERIFY_RESEND |
| subject_hash | char(64) | PK ghép; HMAC IP/email chuẩn hóa, secret ngoài DB |
| window_start | timestamptz | PK ghép, cửa sổ 15 phút |
| request_count | integer | >=0 |

Không id/timestamp. Rate limit theo IP và theo email ở LOGIN/RESET, IP ở REGISTER, user và IP ở resend. Tăng atomically; ngưỡng cấu hình, mặc định login 10/email và 100/IP/15 phút, reset/resend 5/15 phút. Xóa sau 24h. Không khóa vĩnh viễn tài khoản do attacker thử sai.

## 5. Chuyển trạng thái chuẩn

### Job

| Từ | Sang | Điều kiện/hành động |
|---|---|---|
| Mới | DRAFT | Recruiter là member hợp lệ |
| DRAFT / REJECTED | PENDING_APPROVAL | Đủ dữ liệu, company VERIFIED/ACTIVE, email đã xác thực |
| PENDING_APPROVAL | DRAFT | Recruiter thu hồi để sửa |
| PENDING_APPROVAL | PUBLISHED | Admin duyệt, kiểm tra lại deadline/company |
| PENDING_APPROVAL | REJECTED | Admin có lý do |
| PUBLISHED | CLOSED | Recruiter/admin đóng có lý do hoặc system hết hạn |

Published hợp lệ để apply khi company VERIFIED/ACTIVE, deadline > now, job.status=PUBLISHED. Luôn kiểm tra điều kiện này kể cả worker chưa đóng job. Đóng tin không kết thúc application cũ.

### Application

| Từ | Sang | Tác nhân/điều kiện |
|---|---|---|
| Mới | APPLIED | Applicant nộp thành công |
| APPLIED | SCREENING | Recruiter |
| APPLIED / SCREENING / INTERVIEW | INTERVIEW | Tạo lịch; nếu đã INTERVIEW không thêm history cùng trạng thái |
| INTERVIEW | OFFER | Gửi offer, đã có ít nhất một interview COMPLETED; không còn SCHEDULED |
| OFFER | INTERVIEW | Offer bị reject/expired/withdrawn; ghi reason, cho phép thương lượng lại |
| OFFER | HIRED | Recruiter xác nhận; có offer ACCEPTED |
| APPLIED / SCREENING / INTERVIEW / OFFER | REJECTED | Recruiter, reason công khai bắt buộc |
| APPLIED / SCREENING / INTERVIEW / OFFER | WITHDRAWN | Applicant, reason ngắn bắt buộc |

HIRED/REJECTED/WITHDRAWN là cuối; không mở lại. Khi kết thúc reject/withdraw, hủy SCHEDULED interviews, thu hồi DRAFT/SENT offers cùng transaction. ACCEPTED offer giữ nguyên lịch sử, không tự đưa về INTERVIEW.

### Interview và offer

| Đối tượng | Chuyển hợp lệ |
|---|---|
| Interview | SCHEDULED → COMPLETED / CANCELLED / NO_SHOW; đổi lịch giữ SCHEDULED và ghi audit/notification |
| Offer | DRAFT → SENT / WITHDRAWN; SENT → ACCEPTED / REJECTED / WITHDRAWN / EXPIRED |
| Offer đã kết thúc | Bất biến; bản mới tăng sequence_number |
| Interview hoàn tất | Không sửa trong MVP; bổ sung giải trình bằng note |

COMPLETED chỉ khi đã tới starts_at; NO_SHOW chỉ khi đã qua ends_at. Offer chấp nhận đúng deadline không hợp lệ (now >= deadline). Worker và user cùng khóa application rồi offer để không xử lý hai kết quả.

## 6. Index và transaction bắt buộc

| Nhóm | Index/constraint |
|---|---|
| Public search | jobs(status,deadline,created_at DESC,id), jobs(company_id,status), jobs(category_id,location_id); GIN to_tsvector('simple',title + description + requirements) |
| Company | memberships(company_id,left_at), các unique partial ở 4.5; không FK recruiter trực tiếp vào jobs thay company |
| Matching | job_skills(skill_id,job_id), applicant_skills(skill_id,applicant_id) |
| Application | applications(job_id,status,created_at DESC,id), applications(applicant_id,created_at DESC,id), unique cặp applicant/job |
| History | job_status_history(job_id,created_at,id), application_status_history(application_id,created_at,id) |
| Interview/offer | interviews(application_id,status,starts_at), offers(application_id,status), offers(status,response_deadline) |
| Thông báo/worker | notifications(user_id,created_at DESC,id), index partial unread; email_deliveries(status,next_attempt_at), index lease PROCESSING |
| Audit/AI | audit_logs(created_at DESC,id), audit_logs(entity_type,entity_id,created_at); ai_operations(requested_by,feature,input_hash,expires_at) |
| Token | index token hash unique; auth_sessions(user_id,revoked_at); account_tokens(user_id,purpose) |

Tất cả FK thường dùng tra cứu cần index; unique/index ghép đã có tiền tố tương ứng không tạo thêm index trùng.

| Thao tác | Phạm vi atomic |
|---|---|
| Đăng ký | User + applicant (nếu có) + token + email delivery |
| Tạo công ty | Company + OWNER; khóa user chống tạo đồng thời |
| Nhận lời mời | Khóa user/company/invitation; membership + accepted + audit |
| Duyệt/đóng job | Job + history + notifications + email deliveries + audit |
| Apply | Khóa company/job/resume, kiểm tra lại deadline/owner; application + history + notifications |
| Pipeline/interview/offer | Khóa company → application → interview/offer; state + history + notifications + audit |
| CV default/delete | Khóa applicant → resume; bỏ default cũ trước đặt mới |
| Suspension | Khóa company/user tương ứng; trạng thái + thu hồi session + audit; các request ghi kiểm tra lại cùng lock |

Thống nhất thứ tự khóa: user khi cần membership → company → job → applicant khi quản lý CV → application → resume/interview/offer. Use case chỉ khóa những bản ghi cần thiết; không khóa ngược thứ tự. Vi phạm unique/state → HTTP 409; kiểm tra trước trong code không thay thế constraint. expected_version không khớp → 409, client tải lại.

Không giữ transaction khi gọi SMTP, LLM hoặc render PDF. Render/upload file trước, insert metadata sau khi thành công; DB lỗi thì xóa file vừa tạo hoặc đánh dấu cleanup. File mồ côi được quét theo storage_key sau 24 giờ.

## 7. Chính sách dữ liệu và vận hành

| Nội dung | Chính sách MVP |
|---|---|
| Xóa CV | Ẩn ngay khỏi lựa chọn; giữ file đang được application tham chiếu trong thời hạn lưu; không ghi đè. |
| Xóa học vấn/skill | Cho sửa/xóa hồ sơ sống; PDF đã nộp không thay đổi. |
| Xóa job/company/user | Tự phục vụ dùng đóng/đình chỉ/deactivate; không cascade. Yêu cầu xóa dữ liệu cá nhân xử lý thủ công có audit. |
| Retention đề xuất | Hồ sơ đã kết thúc: 12 tháng từ ended_at; sau đó xử lý file/snapshot theo policy được công bố. Đây là lựa chọn sản phẩm cần rà trước dùng dữ liệu thật, không phải thời hạn pháp luật mặc định. |
| Giữ lịch sử | Khi cần xóa PII, xóa file và ẩn danh snapshot/note/output AI liên quan; giữ ID và dữ kiện tổng hợp tối thiểu nếu còn cơ sở lưu giữ. Quy trình có backup expiry rõ. |
| Email/AI | Payload email 7 ngày sau hoàn thành; output AI tối đa 30 ngày, cache 24h; token hết hạn dọn sau 7 ngày. |
| Audit | 12 tháng theo policy demo; không chứa CV, password, token, prompt thô. |
| Backup | Backup PostgreSQL và private files cùng kế hoạch; thử khôi phục trước bàn giao. |
| Danh mục | Seed versioned; không tự thêm skill từ AI; deactivate thay xóa bản ghi đang dùng. |

## 8. Điều kiện để chuyển sang migration

- Mỗi bảng có PK, NULL/default rõ; tạo bảng cha trước bảng con.
- Mọi FK/unique/CHECK/partial index trên đây được thể hiện trong migration.
- Điều kiện liên bảng/role/state đặt ở service transaction; không viết CHECK truy vấn bảng khác.
- Kiểm thử đồng thời: apply trùng, nhận hai lời mời, hai default CV, accept và expire offer, đổi trạng thái từ version cũ.
- Kiểm thử quyền: CV khác chủ, recruiter công ty khác, membership hết hiệu lực, session đã thu hồi.
- Hai tài liệu được cập nhật cùng nhau khi thay đổi nghiệp vụ. Không dùng số lượng bảng làm thước đo hoàn chỉnh.
