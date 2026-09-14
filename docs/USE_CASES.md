# Đặc tả use case Job Portal MVP

Phiên bản 1.0 • 14/09/2026 • Đi kèm [ERD.md](ERD.md).

Hai tài liệu này là baseline triển khai hiện hành, thay phần mô tả nghiệp vụ tương ứng trong SRS/flows/kế hoạch cũ. Các giới hạn thời gian, dung lượng và quota là cấu hình mặc định của MVP.

## 1. Quy tắc áp dụng chung

| Nội dung | Quy tắc |
|---|---|
| Xác thực | 401 khi chưa đăng nhập/token không hợp lệ. 403 khi role hoặc trạng thái tài khoản không cho phép. |
| Quyền tài nguyên | ID không tồn tại hoặc ngoài phạm vi truy cập → 404; không tiết lộ CV/application công ty khác. |
| Quyền recruiter | User ACTIVE + membership chưa left + company ACTIVE; submit/pipeline/CV yêu cầu thêm VERIFIED. OWNER là role trong công ty, không phải role tài khoản mới. |
| Dữ liệu nhập | DTO allowlist; reject trường đặc quyền; trim văn bản; validate type/length/catalog. Không tin company_id/user_id/status client tự khai. |
| HTTP lỗi | 400 token không hợp lệ; 409 xung đột/state/version; 413 file lớn; 415 loại file; 422 dữ liệu; 429 rate limit; 503 dịch vụ tạm lỗi. |
| Body lỗi | `{code, message, field_errors?, request_id}`; thông báo tiếng Việt dễ hiểu, không trả stack trace/SQL/provider secret. |
| Transaction | Mỗi thay đổi trạng thái ghi history/audit/notification tương ứng cùng commit. Lỗi rollback; SMTP/LLM/render không chạy trong transaction. |
| Ghi đồng thời | Đối tượng có version yêu cầu expected_version; khóa và kiểm tra lại quyền/state/deadline trong transaction. Unique DB là lớp chặn cuối. |
| Notification | Gửi applicant và recruiter phụ trách/OWNER liên quan; dedup theo user/event_key. Không broadcast PII cho mọi admin/recruiter. |
| Public/private | Applicant DTO không có notes, feedback nội bộ, offer DRAFT hoặc thông tin xét duyệt công ty. Admin không mặc định tải CV. |
| Ngôn ngữ nội dung | MVP dùng plain text, escape khi hiển thị; render PDF chỉ dùng template/asset nội bộ. |
| Hệ thống khóa | Company SUSPENDED chặn thao tác tuyển dụng và CV của recruiter; applicant vẫn đọc/rút đơn của mình. Offer không accept trong thời gian đình chỉ, vẫn hết hạn theo giờ. |

## 2. Danh sách use case

| Mã | Use case |
|---|---|
| [UC-01](#uc-01) | Đăng ký tài khoản |
| [UC-02](#uc-02) | Xác thực email và gửi lại |
| [UC-03](#uc-03) | Đăng nhập, refresh, đăng xuất |
| [UC-04](#uc-04) | Quên/đặt lại mật khẩu |
| [UC-05](#uc-05) | Tạo hồ sơ công ty |
| [UC-06](#uc-06) | Cập nhật công ty và gửi lại duyệt |
| [UC-07](#uc-07) | Duyệt hoặc đình chỉ công ty |
| [UC-08](#uc-08) | Mời, nhận lời mời và gỡ thành viên |
| [UC-09](#uc-09) | Xem/tìm job và trang công ty |
| [UC-10](#uc-10) | Tạo/sửa/sao chép job nháp |
| [UC-11](#uc-11) | Gửi hoặc thu hồi tin chờ duyệt |
| [UC-12](#uc-12) | Admin duyệt/từ chối job |
| [UC-13](#uc-13) | Đóng tin và xử lý tin hết hạn |
| [UC-14](#uc-14) | Cập nhật hồ sơ, học vấn, kinh nghiệm, kỹ năng |
| [UC-15](#uc-15) | Upload, đặt mặc định, đổi tên và xóa CV |
| [UC-16](#uc-16) | Soạn CV theo mẫu và xuất PDF |
| [UC-17](#uc-17) | Tải CV của mình hoặc CV đã ứng tuyển |
| [UC-18](#uc-18) | Nộp đơn ứng tuyển |
| [UC-19](#uc-19) | Xem danh sách và chi tiết application |
| [UC-20](#uc-20) | Screening, ghi chú, từ chối và xác nhận Hired |
| [UC-21](#uc-21) | Rút đơn ứng tuyển |
| [UC-22](#uc-22) | Tạo/đổi/hủy lịch phỏng vấn |
| [UC-23](#uc-23) | Ghi nhận kết quả phỏng vấn |
| [UC-24](#uc-24) | Tạo/sửa/gửi/thu hồi offer |
| [UC-25](#uc-25) | Xem và phản hồi offer |
| [UC-26](#uc-26) | Offer hết hạn và nhắc lịch |
| [UC-27](#uc-27) | Đọc thông báo |
| [UC-28](#uc-28) | Dashboard và CSV báo cáo |
| [UC-29](#uc-29) | Gợi ý công việc và tính điểm khớp |
| [UC-30](#uc-30) | AI giải thích độ phù hợp |
| [UC-31](#uc-31) | AI soạn mô tả công việc |
| [UC-32](#uc-32) | Admin quản lý user và danh mục |
| [UC-33](#uc-33) | Admin xem audit |
| [UC-34](#uc-34) | Gửi email và phục hồi lỗi worker |
| [UC-35](#uc-35) | Ngừng tài khoản và xử lý dữ liệu cá nhân |

## 3. Đặc tả chi tiết

<a id="uc-01"></a>

### UC-01. Đăng ký tài khoản

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Khách |
| Dữ liệu vào | email, password, full_name; role APPLICANT/RECRUITER; phone bắt buộc recruiter. |
| Kiểm tra | Email hợp lệ <=254; tên 1–150; mật khẩu 15–128 ký tự, không cắt ngắn, chặn mật khẩu phổ biến. Rate limit đăng ký; backend từ chối ADMIN và mọi trường đặc quyền. |
| Luồng thành công/kết quả | Chuẩn hóa email; hash Argon2id; tạo user ACTIVE chưa xác thực; tạo applicant rỗng nếu APPLICANT; token xác thực 24h + email delivery trong transaction. Trả 202 với thông điệp chung. |
| Lỗi và xử lý | Email đã tồn tại: vẫn 202 chung, không tạo user mới/không đổi mật khẩu; định dạng sai 422; rate limit 429; transaction lỗi rollback toàn bộ. |
| Bảng sử dụng | users, applicants, account_tokens, email_deliveries, security_rate_windows. |
| Nghiệm thu tối thiểu | Đăng ký hai lần cùng email chỉ một tài khoản; gửi role ADMIN không tạo admin. |

<a id="uc-02"></a>

### UC-02. Xác thực email và gửi lại

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | User/khách có token |
| Dữ liệu vào | token; gửi lại yêu cầu user đăng nhập. |
| Kiểm tra | Digest tồn tại, purpose VERIFY_EMAIL, chưa dùng, chưa hết hạn; gửi lại không quá 5/15 phút. |
| Luồng thành công/kết quả | Khóa token/user; đặt email_verified_at và consumed_at cùng transaction. Gửi lại vô hiệu token cũ, tạo token 24h và email delivery. Trả 200 hoặc 202 khi gửi lại. |
| Lỗi và xử lý | Token sai/hết hạn/đã dùng: 400 TOKEN_INVALID_OR_EXPIRED, có thể gửi lại. User đã xác thực: 200 không thay đổi. Email lỗi được worker retry. |
| Bảng sử dụng | users, account_tokens, email_deliveries, security_rate_windows. |
| Nghiệm thu tối thiểu | Token không dùng lần hai; xác thực email không tự duyệt công ty. |

<a id="uc-03"></a>

### UC-03. Đăng nhập, refresh, đăng xuất

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Mọi tài khoản |
| Dữ liệu vào | email/password; refresh cookie; session khi logout. |
| Kiểm tra | Thông tin đăng nhập; user ACTIVE; rate limit; refresh đúng digest/phiên/hạn. Kiểm tra Origin và CSRF cho request dựa vào cookie. |
| Luồng thành công/kết quả | Login tạo auth_session, access token 15 phút và refresh 7 ngày. Refresh xoay digest atomically; logout thu hồi phiên hiện tại, trả 204. Access token trong bộ nhớ client, refresh cookie HttpOnly/Secure/SameSite phù hợp deployment. |
| Lỗi và xử lý | Sai thông tin 401 chung; tài khoản khóa 403 sau xác minh credentials; token hết hạn/thu hồi 401; refresh đồng thời một request thắng, request còn lại 401. Client serialize refresh, không retry token cũ vô hạn. |
| Bảng sử dụng | users, auth_sessions, security_rate_windows. |
| Nghiệm thu tối thiểu | Logout xong access token cũ không dùng được; user chưa xác thực chỉ dùng chức năng không yêu cầu email verified. |

<a id="uc-04"></a>

### UC-04. Quên/đặt lại mật khẩu

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Khách |
| Dữ liệu vào | email; token + mật khẩu mới. |
| Kiểm tra | Rate limit; RESET_PASSWORD token chưa dùng/hết hạn 30 phút; password như UC-01. |
| Luồng thành công/kết quả | Yêu cầu reset luôn 202 chung. Nếu email có tài khoản, tạo token/delivery. Khi reset hợp lệ: khóa token, đổi hash, consume token và thu hồi mọi session trong transaction. |
| Lỗi và xử lý | Email không tồn tại vẫn 202; token sai 400 chung; password lỗi 422; mail lỗi retry; không đăng nhập tự động sau reset. |
| Bảng sử dụng | users, account_tokens, auth_sessions, email_deliveries, security_rate_windows. |
| Nghiệm thu tối thiểu | Không dò được tài khoản qua body/status; mọi phiên cũ mất hiệu lực. |

<a id="uc-05"></a>

### UC-05. Tạo hồ sơ công ty

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter ACTIVE, email verified, chưa có membership |
| Dữ liệu vào | name, registration_number, description, industry, size_band, location_id, address; website/logo tùy chọn. |
| Kiểm tra | Mã đăng ký không trùng; catalog active; size_band hợp lệ; tên <=200, địa chỉ <=500, mô tả <=10000; HTTP(S) website. Logo PNG/JPEG <=2MiB, decode/re-encode, không SVG. |
| Luồng thành công/kết quả | Khóa user; tạo companies PENDING/ACTIVE và membership OWNER cùng transaction; audit; báo admin có hồ sơ cần duyệt. Trả 201. |
| Lỗi và xử lý | Đã thuộc công ty/mã đăng ký tồn tại: 409, hướng dẫn xin lời mời hoặc liên hệ admin; không tự gắn vào công ty trùng tên. Upload ảnh lỗi 415/413; DB lỗi dọn ảnh mới. |
| Bảng sử dụng | companies, company_memberships, locations, notifications, audit_logs. |
| Nghiệm thu tối thiểu | Không có công ty mồ côi thiếu OWNER; hai request chỉ tạo tối đa một membership active. |

<a id="uc-06"></a>

### UC-06. Cập nhật công ty và gửi lại duyệt

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | OWNER của công ty ACTIVE |
| Dữ liệu vào | Các trường công ty cho phép. |
| Kiểm tra | Không cho sửa verification_status/status/owner. Khi VERIFIED khóa name/registration_number; khi REJECTED được sửa và gửi lại. |
| Luồng thành công/kết quả | Lưu trường mô tả/quy mô/địa chỉ/logo. REJECTED gửi lại → PENDING, reset reviewed_by/at/note; audit giữ quyết định cũ. Không đổi trạng thái job hiện có. |
| Lỗi và xử lý | MEMBER 403; công ty khác 404; đổi thông tin định danh đã VERIFIED 409; catalog/file sai 422/415. |
| Bảng sử dụng | companies, locations, audit_logs, notifications. |
| Nghiệm thu tối thiểu | Public chỉ thấy DTO công khai; thay ảnh không làm lộ hồ sơ xét duyệt. |

<a id="uc-07"></a>

### UC-07. Duyệt hoặc đình chỉ công ty

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Admin ACTIVE |
| Dữ liệu vào | company_id, action VERIFY/REJECT/SUSPEND/RESTORE, reason. |
| Kiểm tra | VERIFY/REJECT chỉ PENDING; kiểm tra liên hệ/website/mã đăng ký thủ công. Reason bắt buộc reject/suspend; RESTORE không tự biến REJECTED thành VERIFIED. |
| Luồng thành công/kết quả | Khóa company; cập nhật quyết định/hoạt động, audit và notify OWNER. SUSPEND chặn mọi ghi tuyển dụng và tải CV của recruiter; job không nhận application mới. RESTORE phục hồi theo verification/job/deadline hiện tại. |
| Lỗi và xử lý | Sai state 409; thiếu reason 422; không tìm thấy 404. Không tự reject application khi đình chỉ. |
| Bảng sử dụng | companies, company_memberships, notifications, email_deliveries, audit_logs. |
| Nghiệm thu tối thiểu | Đình chỉ có hiệu lực với recruiter đang đăng nhập; applicant vẫn xem hồ sơ của mình và được withdraw. |

<a id="uc-08"></a>

### UC-08. Mời, nhận lời mời và gỡ thành viên

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | OWNER mời/gỡ; recruiter nhận lời mời |
| Dữ liệu vào | email; invitation token; membership_id. |
| Kiểm tra | Company VERIFIED/ACTIVE; email xác thực của người nhận khớp lời mời; role RECRUITER; chưa thuộc công ty; token hạn 7 ngày. Không mời OWNER thứ hai. |
| Luồng thành công/kết quả | Tạo invitation PENDING và email; nhận lời mời khóa user/company/invitation, tạo MEMBER và ACCEPTED atomically. OWNER gỡ MEMBER bằng left_at; có thể revoke lời mời PENDING. |
| Lỗi và xử lý | Trùng lời mời pending/đã thuộc công ty 409; token sai/hết hạn 400; khác email 403; không gỡ OWNER 409. Membership bị gỡ mất quyền ngay. |
| Bảng sử dụng | company_invitations, company_memberships, companies, users, email_deliveries, audit_logs. |
| Nghiệm thu tối thiểu | Không thể nhập company_id để tự nhận quyền; hai lời mời khác công ty chỉ nhận được một. |

<a id="uc-09"></a>

### UC-09. Xem/tìm job và trang công ty

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Khách hoặc user |
| Dữ liệu vào | keyword, category, location, skill_ids, employment_type, work_mode, salary_min/max, page, page_size. |
| Kiểm tra | Keyword <=200; catalog/filter hợp lệ; page>=1; page_size 1–50; sort allowlist newest/salary. Không ghép SQL từ input. |
| Luồng thành công/kết quả | Danh sách chỉ PUBLISHED chưa hết hạn của company VERIFIED/ACTIVE. Tìm full-text simple; nhiều skill lọc ANY; salary filter lấy khoảng giao nhau và loại lương thỏa thuận khi có filter. Chi tiết job đã đóng trả 200 kèm không thể apply; company suspended/job chưa publish trả 404 cho public. Company detail trả mô tả + job đang tuyển. |
| Lỗi và xử lý | Filter sai 422; trang không có dữ liệu 200 danh sách rỗng; tài nguyên không công khai 404. Không yêu cầu đăng nhập chỉ để đọc JD. |
| Bảng sử dụng | jobs, companies, job_categories, locations, job_skills, skills. |
| Nghiệm thu tối thiểu | Không lộ email recruiter, verification_note, CV hoặc draft; sắp xếp ổn định thêm id. |

<a id="uc-10"></a>

### UC-10. Tạo/sửa/sao chép job nháp

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter có membership active, company ACTIVE |
| Dữ liệu vào | title và các trường job; skill_ids; expected_version khi sửa. |
| Kiểm tra | Chỉ sửa DRAFT/REJECTED; kiểm tra type/length/range kể cả draft; không nhận company_id/created_by/status tùy ý từ client. |
| Luồng thành công/kết quả | Tạo DRAFT với company suy ra từ membership. Sửa tăng version; giữ REJECTED đến lúc gửi lại. Sao chép job cùng công ty thành DRAFT, title/nội dung/skills sao chép; deadline đặt NULL và metadata duyệt reset. Tạo history lúc tạo. |
| Lỗi và xử lý | Job khác công ty 404; state/version sai 409; dữ liệu sai 422. User thuộc company PENDING có thể soạn draft nhưng chưa submit. |
| Bảng sử dụng | jobs, job_skills, job_status_history, company_memberships. |
| Nghiệm thu tối thiểu | Không sửa PUBLISHED; copy không mang theo application hoặc quyết định duyệt. |

<a id="uc-11"></a>

### UC-11. Gửi hoặc thu hồi tin chờ duyệt

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter cùng công ty |
| Dữ liệu vào | job_id, expected_version; action SUBMIT/RECALL. |
| Kiểm tra | Submit: email verified, company VERIFIED/ACTIVE; đủ trường ở ERD 4.16; 1–30 skill active; deadline tương lai; lương hợp lệ. Recall chỉ PENDING_APPROVAL. |
| Luồng thành công/kết quả | Khóa company/job; SUBMIT → PENDING_APPROVAL, RECALL → DRAFT; tăng version, history, audit, notify admin khi submit. |
| Lỗi và xử lý | Thiếu dữ liệu 422 với field_errors; deadline quá hạn 422; công ty chưa duyệt 403; admin vừa duyệt trước recall →409. |
| Bảng sử dụng | jobs, job_skills, companies, job_status_history, notifications, audit_logs. |
| Nghiệm thu tối thiểu | Không có job publish trước admin; race recall/approve chỉ một thao tác thành công. |

<a id="uc-12"></a>

### UC-12. Admin duyệt/từ chối job

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Admin ACTIVE |
| Dữ liệu vào | job_id, APPROVE/REJECT, expected_version, reason. |
| Kiểm tra | Job PENDING_APPROVAL; company VERIFIED/ACTIVE; kiểm tra nội dung, deadline vẫn còn; reason bắt buộc reject. |
| Luồng thành công/kết quả | Khóa company/job; approve →PUBLISHED và published_at; reject →REJECTED; history + audit + notify recruiter tạo tin và OWNER, deduplicate người trùng. |
| Lỗi và xử lý | Sai state/version 409; hết hạn/thiếu nội dung 422; không đủ điều kiện company 409. UI tải lại khi có xung đột. |
| Bảng sử dụng | jobs, job_status_history, companies, notifications, email_deliveries, audit_logs. |
| Nghiệm thu tối thiểu | Hai admin không duyệt hai lần; email lỗi không rollback quyết định đã commit. |

<a id="uc-13"></a>

### UC-13. Đóng tin và xử lý tin hết hạn

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter cùng công ty/Admin; worker |
| Dữ liệu vào | job_id/version/reason; worker quét deadline. |
| Kiểm tra | Đóng tay chỉ PUBLISHED; reason bắt buộc. Worker chỉ đóng PUBLISHED có deadline<=now. |
| Luồng thành công/kết quả | Cập nhật CLOSED/closed_at/closure_reason, history và notification. Worker chạy mỗi phút theo lô. Application cũ tiếp tục xử lý nếu company ACTIVE. |
| Lỗi và xử lý | Đã CLOSED trả 200 trạng thái hiện tại; state khác 409. Worker lỗi retry; API apply vẫn kiểm tra deadline trực tiếp. |
| Bảng sử dụng | jobs, job_status_history, notifications, audit_logs. |
| Nghiệm thu tối thiểu | Tin hết hạn không nhận hồ sơ dù worker dừng; đóng job không reject hàng loạt. |

<a id="uc-14"></a>

### UC-14. Cập nhật hồ sơ, học vấn, kinh nghiệm, kỹ năng

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant của hồ sơ |
| Dữ liệu vào | headline/summary/địa điểm/kỳ vọng; education[]/experience[]/skill_ids. |
| Kiểm tra | Owner từ user hiện tại; text summary<=5000; năm kinh nghiệm>=0; lương max>=min; tối đa 50 skills, 20 education, 30 experience; ngày hợp lệ; skill active. |
| Luồng thành công/kết quả | CRUD hồ sơ và các mục con; chỉnh name/phone tại users; email không đổi qua API profile. Khi thay danh sách skills, cập nhật trong transaction. Không sửa CV hoặc application cũ. |
| Lỗi và xử lý | ID mục con của người khác 404; catalog/date/range sai 422. Không yêu cầu điền đầy đủ mọi trường để lưu. |
| Bảng sử dụng | users, applicants, applicant_educations, applicant_experiences, applicant_skills. |
| Nghiệm thu tối thiểu | Sửa hồ sơ không đổi file CV hoặc snapshot của application đã nộp. |

<a id="uc-15"></a>

### UC-15. Upload, đặt mặc định, đổi tên và xóa CV

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant email verified |
| Dữ liệu vào | file; resume_id; title; set_default/delete. |
| Kiểm tra | Tối đa 10 CV chưa xóa/applicant; file <=5MiB; extension+MIME+signature nhất quán; PDF/DOC/DOCX; kiểm tra cấu trúc DOCX và giới hạn giải nén. File parser chạy có timeout, không thực thi nội dung. |
| Luồng thành công/kết quả | Lưu private bằng key ngẫu nhiên, metadata sau thành công; file đầu tiên mặc định. Đặt default khóa applicant, bỏ default cũ trước. Xóa đặt deleted_at và is_default=false; không tự chọn default khác. |
| Lỗi và xử lý | Sai file 415; lớn 413; đủ quota 409; file khác chủ 404; storage lỗi 503 không tạo metadata; DB lỗi dọn file. CV đã nộp vẫn giữ file theo retention. |
| Bảng sử dụng | resumes, applicants; applications dùng kiểm tra retention. |
| Nghiệm thu tối thiểu | Không ghi đè file; hai request đặt default không tạo hai default; CV xóa không còn chọn apply. |

<a id="uc-16"></a>

### UC-16. Soạn CV theo mẫu và xuất PDF

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant email verified |
| Dữ liệu vào | title, content CV_V1, revision; template BASIC_V1. |
| Kiểm tra | Tối đa 10 bản soạn chưa xóa; contact name/email/phone bắt buộc khi xuất; giới hạn mỗi section như UC-14; projects<=20; text tổng<=50000; không HTML/script/remote assets. |
| Luồng thành công/kết quả | Tạo/sửa cv_documents, revision tăng; xuất snapshot revision bằng template cố định ngoài DB transaction; lưu PDF mới GENERATED trong resumes, liên kết revision. Không tự đổi default. Bản soạn có thể xóa mềm. |
| Lỗi và xử lý | Revision cũ 409; dữ liệu sai 422; render quá 15s/lỗi 503 không tạo resume. Retry có thể tạo file mới; quota CV áp dụng như upload. CV đã xuất không sửa theo bản soạn. |
| Bảng sử dụng | cv_documents, resumes, applicants. |
| Nghiệm thu tối thiểu | Xuất revision 2 không làm thay đổi application đã dùng file revision 1. |

<a id="uc-17"></a>

### UC-17. Tải CV của mình hoặc CV đã ứng tuyển

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant sở hữu / Recruiter cùng company của application |
| Dữ liệu vào | resume_id cho chủ; application_id cho recruiter. |
| Kiểm tra | User active; recruiter membership và company VERIFIED/ACTIVE; file đúng resume_id đã nộp vào application đó. Không cấp quyền xem tất cả CV của applicant. |
| Luồng thành công/kết quả | Kiểm tra quyền trước truy cập storage; ghi CV_DOWNLOAD_AUTHORIZED rồi stream attachment với nosniff và tên làm sạch. CV soft-delete vẫn tải qua application nếu chưa hết retention. |
| Lỗi và xử lý | Không có quyền tài nguyên 404; file đã purge/mất 410 FILE_UNAVAILABLE với thông báo liên hệ hỗ trợ; storage tạm lỗi 503; audit ghi không được thì không cấp tải. |
| Bảng sử dụng | resumes, applications, jobs, companies, company_memberships, audit_logs. |
| Nghiệm thu tối thiểu | Recruiter A đổi application_id sang company B bị từ chối; admin không có quyền đọc CV mặc định. |

<a id="uc-18"></a>

### UC-18. Nộp đơn ứng tuyển

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant ACTIVE, email verified |
| Dữ liệu vào | job_id, resume_id, contact_name, contact_phone, cover_letter tùy chọn. |
| Kiểm tra | Job PUBLISHED/deadline>now/company VERIFIED ACTIVE; resume cùng chủ chưa deleted; name/phone hợp lệ; cover<=3000; chưa có cặp applicant/job. |
| Luồng thành công/kết quả | Khóa company/job và resume theo thứ tự; kiểm tra lại điều kiện; tạo application APPLIED với contact_email từ tài khoản; history ban đầu + notification cho applicant/recruiter liên quan và email delivery. Trả 201. |
| Lỗi và xử lý | Job đóng/hết hạn/đã apply:409 với mã riêng; CV khác chủ404; validation422. Unique race→409 APPLICATION_EXISTS; request mạng đứt thì client đọc danh sách trước thử lại. |
| Bảng sử dụng | applications, application_status_history, resumes, jobs, companies, notifications, email_deliveries. |
| Nghiệm thu tối thiểu | Nộp đồng thời chỉ một đơn; đổi CV default sau apply không đổi resume_id đơn. |

<a id="uc-19"></a>

### UC-19. Xem danh sách và chi tiết application

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant hoặc recruiter hợp lệ |
| Dữ liệu vào | job_id/status/page; application_id. |
| Kiểm tra | Applicant chỉ của mình; recruiter chỉ job company mình; filter status allowlist; page_size<=50. |
| Luồng thành công/kết quả | Applicant thấy snapshot nộp, job/company, history công khai, lịch và offer đã gửi. Recruiter thấy snapshot và hồ sơ hiện tại được ghi nhãn riêng, CV đã nộp, history và ghi chú nội bộ. Public DTO không lộ feedback, DRAFT offer hoặc notes. |
| Lỗi và xử lý | Khác chủ/công ty404; filter sai422. Applicant vẫn đọc đơn của mình khi company đình chỉ. |
| Bảng sử dụng | applications, application_status_history, jobs, applicants, application_notes, interviews, offers. |
| Nghiệm thu tối thiểu | Response applicant không chứa field nội bộ ngay cả khi frontend không hiển thị. |

<a id="uc-20"></a>

### UC-20. Screening, ghi chú, từ chối và xác nhận Hired

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter company VERIFIED/ACTIVE |
| Dữ liệu vào | application_id, action, expected_version; reason/note. |
| Kiểm tra | Bảng state ở ERD mục5; SCREENING từ APPLIED; note1–3000; reject reason1–1000; HIRED chỉ OFFER có ACCEPTED offer. Không có API set status tùy ý. |
| Luồng thành công/kết quả | Khóa company/application; transition tăng version + history + notification/audit. Reject hủy interview SCHEDULED, thu hồi DRAFT/SENT offer; note append-only không notify applicant. HIRED đặt ended_at. |
| Lỗi và xử lý | Sai state/version409; thiếu lý do422; khác company404. Không cho chỉnh lịch sử hoặc đổi status application đã kết thúc. |
| Bảng sử dụng | applications, application_status_history, application_notes, interviews, offers, notifications, audit_logs. |
| Nghiệm thu tối thiểu | Accept offer chưa tự HIRED; recruiter xác nhận mới ghi Hired. |

<a id="uc-21"></a>

### UC-21. Rút đơn ứng tuyển

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant sở hữu |
| Dữ liệu vào | application_id, reason, expected_version. |
| Kiểm tra | APPLIED/SCREENING/INTERVIEW/OFFER; user ACTIVE; không cần company ACTIVE để rút. Reason1–1000. |
| Luồng thành công/kết quả | Khóa application; WITHDRAWN + ended_at; hủy interview SCHEDULED, thu hồi DRAFT/SENT offer, giữ ACCEPTED offer lịch sử; history + notifications. Không thể apply lại cùng job. |
| Lỗi và xử lý | Đã WITHDRAWN trả200; state terminal khác hoặc version cũ409; khác chủ404. |
| Bảng sử dụng | applications, application_status_history, interviews, offers, notifications, audit_logs. |
| Nghiệm thu tối thiểu | Rút sau accept trước Hired hợp lệ; offer accepted giữ dấu vết đã chấp nhận. |

<a id="uc-22"></a>

### UC-22. Tạo/đổi/hủy lịch phỏng vấn

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter cùng công ty |
| Dữ liệu vào | application_id; round_number, starts_at/ends_at, mode, meeting_url/address, interviewer_name; version khi sửa. |
| Kiểm tra | Application APPLIED/SCREENING/INTERVIEW; tạo/đổi lịch tương lai; thời lượng<=8h; không overlap SCHEDULED cùng application; URL HTTP(S) không fetch; hủy cần reason. Sửa/hủy chỉ SCHEDULED. |
| Luồng thành công/kết quả | Khóa application; tạo interview SCHEDULED; application→INTERVIEW nếu chưa ở đó; sửa lịch tăng version; hủy→CANCELLED không lùi application. Ghi audit và notify applicant/recruiter. |
| Lỗi và xử lý | Trùng vòng/lịch/version409; giờ/địa chỉ/URL sai422; application OFFER/terminal409. Không kiểm tra lịch Google hoặc lịch toàn bộ interviewer. |
| Bảng sử dụng | interviews, applications, application_status_history, notifications, email_deliveries, audit_logs. |
| Nghiệm thu tối thiểu | Hai request trùng giờ bị chặn; applicant nhận thông báo lịch mới khi dời lịch. |

<a id="uc-23"></a>

### UC-23. Ghi nhận kết quả phỏng vấn

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter cùng công ty |
| Dữ liệu vào | interview_id, COMPLETED/NO_SHOW, result, feedback, expected_version. |
| Kiểm tra | Interview SCHEDULED; COMPLETED đã tới starts_at và result bắt buộc; NO_SHOW đã qua ends_at; application chưa terminal; feedback<=5000. |
| Luồng thành công/kết quả | Khóa application/interview; cập nhật trạng thái/result/feedback; audit; applicant chỉ thấy trạng thái lịch. PASS/FAIL không tự chuyển application hoặc loại ứng viên. |
| Lỗi và xử lý | Sai thời điểm422; đã hoàn tất/version cũ409; khác company404. |
| Bảng sử dụng | interviews, applications, audit_logs. |
| Nghiệm thu tối thiểu | Feedback không xuất hiện trong API applicant; muốn reject cần UC-20 riêng. |

<a id="uc-24"></a>

### UC-24. Tạo/sửa/gửi/thu hồi offer

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter cùng công ty |
| Dữ liệu vào | application_id; salary, start_date, response_deadline, terms; expected_version. |
| Kiểm tra | Tạo khi INTERVIEW; ít nhất một COMPLETED interview; không còn SCHEDULED; không có DRAFT/SENT/ACCEPTED offer. Lương>0; deadline tương lai; start_date không trước ngày deadline theo Asia/Ho_Chi_Minh. Sửa chỉ DRAFT. |
| Luồng thành công/kết quả | Khóa application; tạo DRAFT sequence kế tiếp. Gửi kiểm tra lại toàn bộ, SENT/sent_at và application OFFER + history/notification. Thu hồi DRAFT/SENT có reason; từ SENT đưa application INTERVIEW. Giữ nội dung offer cũ. |
| Lỗi và xử lý | Có offer hoạt động/đã accepted409; dữ liệu422; version409. Offer SENT quá hạn: xử lý EXPIRED trước rồi trả409 OFFER_EXPIRED, không đổi terms. |
| Bảng sử dụng | offers, applications, application_status_history, notifications, email_deliveries, audit_logs. |
| Nghiệm thu tối thiểu | Hai offer không cùng SENT; gửi thất bại do email vẫn giữ SENT và email được retry. |

<a id="uc-25"></a>

### UC-25. Xem và phản hồi offer

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant sở hữu |
| Dữ liệu vào | offer_id, ACCEPT/REJECT, note tùy chọn, expected_version. |
| Kiểm tra | Chỉ SENT, chưa hết hạn; application OFFER; company ACTIVE/VERIFIED; note<=1000. Applicant không đọc DRAFT. |
| Luồng thành công/kết quả | Khóa company/application/offer; kiểm tra giờ sau lấy lock; ACCEPT→ACCEPTED/responded_at, application giữ OFFER. REJECT→REJECTED/responded_at, application INTERVIEW với history reason; notify recruiter. Đọc lại để xác nhận kết quả. |
| Lỗi và xử lý | Quá hạn: atomically EXPIRED + application INTERVIEW, commit rồi trả409 OFFER_EXPIRED; company suspended403 và có thể rút đơn qua UC-21; version/state sai409. Lặp phản hồi đã xử lý trả409 kèm current_state. |
| Bảng sử dụng | offers, applications, application_status_history, notifications, audit_logs. |
| Nghiệm thu tối thiểu | Accept và expire đồng thời chỉ một kết quả; applicant không chấp nhận offer người khác. |

<a id="uc-26"></a>

### UC-26. Offer hết hạn và nhắc lịch

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Worker nội bộ |
| Dữ liệu vào | Thời gian hiện tại; batch offer/interview. |
| Kiểm tra | Offer SENT deadline<=now; nhắc offer còn hạn trong24h, interview SCHEDULED bắt đầu trong24h; không nhắc application terminal/company suspended. |
| Luồng thành công/kết quả | Khóa application rồi offer, kiểm tra lại; expire→EXPIRED và application OFFER→INTERVIEW; notify. Nhắc một lần/entity bằng event_key. Worker mỗi phút; bảng email tách khỏi transaction nghiệp vụ. |
| Lỗi và xử lý | Worker dừng không khiến offer quá hạn được accept; job chạy lại dedup notification; trạng thái vừa thay đổi thì bỏ qua. |
| Bảng sử dụng | offers, interviews, applications, application_status_history, notifications, email_deliveries. |
| Nghiệm thu tối thiểu | Chạy worker hai lần không sinh hai in-app reminders; email có giới hạn at-least-once đã nêu. |

<a id="uc-27"></a>

### UC-27. Đọc thông báo

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | User đăng nhập |
| Dữ liệu vào | page/page_size; notification_id hoặc mark_all_read. |
| Kiểm tra | Chỉ user_id hiện tại; page_size<=50. |
| Luồng thành công/kết quả | Danh sách theo created_at/id; đọc đặt read_at nếu NULL; mark_all_read chỉ bản ghi của user tại thời điểm request. Trả200/204. |
| Lỗi và xử lý | Thông báo người khác404; tài nguyên liên kết đã mất quyền thì API đích404, không bỏ kiểm tra quyền vì có notification. |
| Bảng sử dụng | notifications. |
| Nghiệm thu tối thiểu | Không đánh dấu thông báo người khác; read lần hai không tạo sự kiện mới. |

<a id="uc-28"></a>

### UC-28. Dashboard và CSV báo cáo

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant/Recruiter/Admin |
| Dữ liệu vào | date_from/date_to, job_id tùy quyền. |
| Kiểm tra | Khoảng thời gian tối đa366 ngày; recruiter company ACTIVE và job của mình; CSV chỉ admin/recruiter, tối đa10000 dòng. |
| Luồng thành công/kết quả | Applicant đếm application mình theo state. Recruiter đếm job/pipeline/interview/offer công ty. Admin tổng hợp toàn hệ thống. Khoảng lọc [from,to); application volume theo created_at, hires theo history→HIRED; không gọi stage count là conversion rate. CSV escape ô bắt đầu =,+,-,@ và không xuất CV/contact/notes. |
| Lỗi và xử lý | Sai khoảng422; quá giới hạn export422 yêu cầu thu hẹp; khác company404. Không cần BI hoặc báo cáo cohort trong MVP. |
| Bảng sử dụng | jobs, applications, application_status_history, interviews, offers, companies, users. |
| Nghiệm thu tối thiểu | Số dashboard và CSV cùng bộ lọc khớp; CSV không chứa dữ liệu nhạy cảm ngoài mục đích tổng hợp. |

<a id="uc-29"></a>

### UC-29. Gợi ý công việc và tính điểm khớp

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant đăng nhập |
| Dữ liệu vào | limit1–20; job_id khi xem điểm riêng. |
| Kiểm tra | Hồ sơ của mình; job còn nhận đơn/company hợp lệ; danh sách loại job đã apply. |
| Luồng thành công/kết quả | Skill=trùng/tổng skill job; location=1 nếu preferred_location khớp hoặc cả job và preference REMOTE, ngược lại0; salary=1 nếu khoảng giao nhau, ngược lại0. Trọng số0.60/0.25/0.15; thành phần không đủ dữ liệu được loại và chuẩn hóa phần còn lại. Có location nhưng preference chưa nhập thì không dùng nơi cư trú thay thế. Tất cả thiếu: trả job mới, score=null, nhắc bổ sung hồ sơ. Sort score rồi published_at/id. |
| Lỗi và xử lý | Không skill profile thì skill thành phần không khả dụng; job thỏa thuận thì salary không khả dụng; API lọc lại trước trả kết quả. Không job phù hợp trả200 rỗng; không chia0. |
| Bảng sử dụng | applicants, applicant_skills, job_skills, jobs, companies. |
| Nghiệm thu tối thiểu | Điểm có matched/missing skills và criteria_used; không biểu diễn score là xác suất được tuyển. |

<a id="uc-30"></a>

### UC-30. AI giải thích độ phù hợp

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Applicant email verified |
| Dữ liệu vào | job_id. |
| Kiểm tra | Job public còn nhận đơn; hồ sơ mình; input tối thiểu gồm skill tags/title đã làm sạch, điểm UC-29; kiểm tra quyền trước cache; quota20/user/feature/ngày. |
| Luồng thành công/kết quả | Tạo canonical input hash có scoring/prompt version; cache hit trả ngay. Cache miss reserve quota atomically; gọi LLM timeout10s ngoài transaction; validate output {summary, strengths[], gaps[]} với giới hạn. Lưu ai_operation rồi trả cùng score tính sẵn. Cache24h. |
| Lỗi và xử lý | Provider lỗi/timeout/output sai: trả200 source=RULE_BASED với giải thích xác định và ghi FAILED; quota429 kèm fallback; không lưu prompt thô, không gửi contact/file. Input thay đổi làm hash đổi. |
| Bảng sử dụng | ai_operations, ai_rate_windows, các bảng UC-29. |
| Nghiệm thu tối thiểu | LLM không sửa score; job/applicant khác quyền không đọc được cache. |

<a id="uc-31"></a>

### UC-31. AI soạn mô tả công việc

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Recruiter email verified, member company ACTIVE |
| Dữ liệu vào | title, skill_ids, seniority, bullets, benefits tùy chọn; job_id nháp tùy chọn. |
| Kiểm tra | Title<=200; bullets<=3000; skill active; job nếu có phải DRAFT/REJECTED thuộc company. Không gửi contact/PII; quota riêng20/ngày. |
| Luồng thành công/kết quả | Canonical hash; cache theo user; reserve quota; LLM timeout15s trả JSON description/requirements/benefits. Validate plain text/length, lưu ai_operation. Trả bản đề xuất; recruiter lưu vào job qua UC-10. |
| Lỗi và xử lý | Timeout/output sai:200 source=TEMPLATE với khung viết tay; quota429 kèm template; provider errors không publish/sửa job. Không suy diễn phúc lợi hoặc mức lương như dữ kiện chắc chắn. |
| Bảng sử dụng | ai_operations, ai_rate_windows, skills; jobs chỉ đọc. |
| Nghiệm thu tối thiểu | Gọi AI không tự tạo/publish job; output không được thực thi như HTML/SQL. |

<a id="uc-32"></a>

### UC-32. Admin quản lý user và danh mục

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Admin ACTIVE |
| Dữ liệu vào | user_id + SUSPEND/RESTORE; reason; catalog item create/edit/deactivate. |
| Kiểm tra | Không tự khóa mình; không khóa admin cuối cùng; OWNER công ty đang ACTIVE phải đình chỉ công ty trước; email/role không sửa ở endpoint này. Catalog normalized name/code unique. |
| Luồng thành công/kết quả | Khóa user + session khi suspend; revoke mọi session, audit và notify. Restore ACTIVE, không tự phục hồi session cũ. Catalog sửa/deactivate; giữ FK lịch sử, job đã đăng không tự mất skill. |
| Lỗi và xử lý | Vi phạm điều kiện409; lý do thiếu422; catalog trùng409. Không cấp role admin qua cập nhật user. |
| Bảng sử dụng | users, auth_sessions, companies, company_memberships, locations, job_categories, skills, audit_logs. |
| Nghiệm thu tối thiểu | Token cũ của tài khoản bị khóa mất quyền; catalog deactivate không phá hồ sơ cũ. |

<a id="uc-33"></a>

### UC-33. Admin xem audit

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Admin ACTIVE |
| Dữ liệu vào | action, entity_type/id, date range, page. |
| Kiểm tra | Filter allowlist, tối đa366 ngày, page_size<=100. |
| Luồng thành công/kết quả | Đọc log phân trang theo created_at/id; hiển thị actor/action/outcome/request_id/metadata allowlist. Không có API sửa/xóa log trong MVP. |
| Lỗi và xử lý | Filter422; non-admin403; không trả token/prompt/CV raw. |
| Bảng sử dụng | audit_logs, users. |
| Nghiệm thu tối thiểu | CV_DOWNLOAD_AUTHORIZED được hiểu là đã cấp quyền tải, không là tải hoàn tất. |

<a id="uc-34"></a>

### UC-34. Gửi email và phục hồi lỗi worker

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | Worker nội bộ |
| Dữ liệu vào | Delivery đến hạn. |
| Kiểm tra | Claim bằng SKIP LOCKED; lease2 phút; template allowlist; giải mã payload chỉ tại worker; không log token/link. |
| Luồng thành công/kết quả | Đặt PROCESSING, commit; gửi SMTP ngoài transaction; thành công SENT/sent_at. Lỗi tăng attempts, retry1/5/15/60 phút; đủ5 lần FAILED. Lease hết hạn được claim lại. Admin vận hành có thể retry có audit, không cần UI riêng. |
| Lỗi và xử lý | SMTP lỗi không rollback user/job/application. Payload hết hạn hoặc token consumed thì bỏ gửi và đánh dấu FAILED với mã an toàn; cảnh báo vận hành khi hết retry. |
| Bảng sử dụng | email_deliveries, account_tokens/company_invitations khi mail token, audit_logs. |
| Nghiệm thu tối thiểu | Worker chết không giữ delivery vô hạn; không cam kết email exactly-once. |

<a id="uc-35"></a>

### UC-35. Ngừng tài khoản và xử lý dữ liệu cá nhân

| Mục | Đặc tả |
|---|---|
| Tác nhân/tiền điều kiện | User của mình; admin vận hành xử lý retention |
| Dữ liệu vào | Yêu cầu deactivate, password xác nhận; yêu cầu xóa qua kênh hỗ trợ. |
| Kiểm tra | Không deactivate OWNER khi company còn ACTIVE; applicant phải withdraw các đơn đang xử lý trước; không hard-delete từ API. |
| Luồng thành công/kết quả | Deactivate đặt DEACTIVATED và revoke sessions, audit. Yêu cầu xóa thực hiện theo policy: xác định file/snapshot/contact/AI output liên quan, hạn lưu và backup; xóa/ẩn danh có kiểm tra rồi ghi audit không chứa PII. Không cascade mất báo cáo. |
| Lỗi và xử lý | Còn đơn hoạt động/owner chưa xử lý409 kèm bước cần làm; password sai401; lỗi xóa storage phải retry, không báo đã xóa hoàn tất. |
| Bảng sử dụng | users, auth_sessions, applicants, resumes, cv_documents, applications, ai_operations, email_deliveries, audit_logs. |
| Nghiệm thu tối thiểu | Soft-delete không được báo là xóa vĩnh viễn; chỉ xác nhận hoàn tất khi cả storage và DB đã xử lý. |

## 4. Bộ kiểm thử xuyên suốt trước bàn giao

| Kịch bản | Kết quả bắt buộc |
|---|---|
| Recruiter đăng ký → công ty → job → admin duyệt | Job chỉ công khai sau cả company và job đủ điều kiện. |
| Applicant tạo PDF → apply → sửa CV → recruiter tải | Recruiter nhận file cũ đã nộp, không phải bản mới. |
| Apply hai request đồng thời | Một application; một request 201, request còn lại 409. |
| Recruiter đổi application_id sang công ty khác | 404 và không đọc được metadata/file. |
| Đóng job khi vẫn còn ứng viên | Chặn đơn mới, tiếp tục xử lý đơn cũ. |
| Interview → offer reject → offer mới → accept → xác nhận hired | Lưu hai offer; chỉ lần chấp nhận cuối dùng xác nhận Hired; history đầy đủ. |
| Applicant rút khi offer đang SENT | WITHDRAWN, offer bị thu hồi; không thể accept sau đó. |
| Accept offer đồng thời với worker expire | Một kết quả cuối nhất quán; không hai notification mâu thuẫn. |
| Suspend user/company sau login | Quyền ghi và tải CV bị chặn với token cũ. |
| Email/LLM lỗi | Nghiệp vụ đã commit không mất; mail retry; AI có fallback theo use case. |
| Gửi lời mời tới recruiter đang thuộc công ty khác | Không tạo membership thứ hai. |
| Mark notification/read hoặc download dùng ID người khác | Không lộ hay sửa dữ liệu. |
| Restore backup | Khôi phục được cả metadata và file CV liên quan. |

## 5. Thứ tự triển khai

1. Migration/catalog → auth/session → company/membership/approval.
2. Job draft/approval/public search → applicant profile/upload CV → apply.
3. Pipeline/interview/offer → notifications/email worker/audit.
4. CV template PDF → recommendation → LLM explanation/JD.
5. Dashboard/CSV → kiểm thử quyền, transaction đồng thời và phục hồi backup.

Dùng từng dòng “Nghiệm thu tối thiểu” làm integration test; thêm unit test cho state machine, matching, validation và policy quyền. Không cần chờ giao diện hoàn thiện để kiểm thử qua FastAPI/OpenAPI.
