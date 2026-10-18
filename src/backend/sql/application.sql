

-- Lấy applications theo ID để Python kiểm tra quyền và dữ liệu.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_application_by_id(p_id uuid)
RETURNS SETOF public.applications
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.applications AS t
    WHERE t.id = p_id;
$$;

-- Lấy và khóa dòng applications tới cuối transaction, tránh cập nhật đồng thời.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_application(p_id uuid)
RETURNS SETOF public.applications
LANGUAGE sql
AS $$
SELECT t.* FROM public.applications AS t
    WHERE t.id = p_id
    FOR UPDATE;
$$;

-- Tìm application trùng của cùng applicant/job.
-- Đầu vào: job_id, applicant_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.find_application_for_job(p_job_id uuid,
    p_applicant_id uuid)
RETURNS SETOF public.applications
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.applications AS t
    WHERE t.job_id = p_job_id AND t.applicant_id = p_applicant_id;
$$;

-- Tạo application và metadata snapshot CV; Python quản lý file snapshot.
-- Đầu vào: job_id, applicant_id, resume_id, cover_letter, resume_snapshot.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_application(p_job_id uuid,
    p_applicant_id uuid,
    p_resume_id uuid,
    p_cover_letter text,
    p_resume_snapshot jsonb)
RETURNS SETOF public.applications
LANGUAGE sql
AS $$
INSERT INTO public.applications (id, job_id, applicant_id, resume_id, cover_letter, resume_snapshot)
    VALUES (gen_random_uuid(), p_job_id, p_applicant_id, p_resume_id, p_cover_letter, p_resume_snapshot)
    RETURNING *;
$$;

-- Lưu trạng thái application sau khi Python kiểm tra chuyển trạng thái.
-- Đầu vào: id, status.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_application_status(p_id uuid,
    p_status text)
RETURNS SETOF public.applications
LANGUAGE sql
AS $$
UPDATE public.applications
    SET status = p_status,
        updated_at = now()
    WHERE id = p_id
    RETURNING *;
$$;

-- Lưu ghi chú nội bộ; Python chặn applicant đọc trường này.
-- Đầu vào: id, recruiter_note.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_application_note(p_id uuid,
    p_recruiter_note text)
RETURNS SETOF public.applications
LANGUAGE sql
AS $$
UPDATE public.applications
    SET recruiter_note = p_recruiter_note,
        updated_at = now()
    WHERE id = p_id
    RETURNING *;
$$;

-- Ghi history cùng transaction đổi trạng thái application.
-- Đầu vào: application_id, actor_id, from_status, to_status, note.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_application_history(p_application_id uuid,
    p_actor_id uuid,
    p_from_status text,
    p_to_status text,
    p_note text)
RETURNS SETOF public.application_status_history
LANGUAGE sql
AS $$
INSERT INTO public.application_status_history (id, application_id, actor_id, from_status, to_status, note)
    VALUES (gen_random_uuid(), p_application_id, p_actor_id, p_from_status, p_to_status, p_note)
    RETURNING *;
$$;

-- Đọc lịch sử application; Python lọc ghi chú nội bộ theo người gọi.
-- Đầu vào: application_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_application_history(p_application_id uuid)
RETURNS SETOF public.application_status_history
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.application_status_history AS t
    WHERE t.application_id = p_application_id
    ORDER BY t.created_at, t.id;
$$;

-- Applicant xem đơn chính chủ có phân trang.
-- Đầu vào: applicant_id, limit, offset.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_applicant_applications(p_applicant_id uuid,
    p_limit integer,
    p_offset integer)
RETURNS SETOF public.applications
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.applications AS t
    WHERE t.applicant_id = p_applicant_id
    ORDER BY t.created_at DESC, t.id
    LIMIT p_limit OFFSET p_offset;
$$;

-- Recruiter xem đơn theo job thuộc company mình, có phân trang.
-- Đầu vào: job_id, limit, offset.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_job_applications(p_job_id uuid,
    p_limit integer,
    p_offset integer)
RETURNS SETOF public.applications
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.applications AS t
    WHERE t.job_id = p_job_id
    ORDER BY t.created_at DESC, t.id
    LIMIT p_limit OFFSET p_offset;
$$;
