

-- Khóa scheduling trong transaction để hai request không đặt lịch trùng đồng thời.
-- Đầu vào: không có.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_interview_schedule()
RETURNS void
LANGUAGE sql
AS $$
SELECT pg_advisory_xact_lock(806001);
$$;

-- Đọc interview theo ID; quyền được kiểm tra qua application ở Python.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_interview_by_id(p_id uuid)
RETURNS SETOF public.interviews
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.interviews AS t
    WHERE t.id = p_id;
$$;

-- Đọc các vòng interview; Python lọc feedback nội bộ theo role.
-- Đầu vào: application_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_application_interviews(p_application_id uuid)
RETURNS SETOF public.interviews
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.interviews AS t
    WHERE t.application_id = p_application_id
    ORDER BY t.round_number;
$$;

-- Đọc lịch liên quan trước giờ kết thúc; Python kiểm tra khoảng thời gian chồng nhau.
-- Đầu vào: company_id, applicant_id, end_at.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_conflicting_interview_candidates(p_company_id uuid,
    p_applicant_id uuid,
    p_end_at timestamptz)
RETURNS SETOF public.interviews
LANGUAGE sql STABLE
AS $$
SELECT i.* FROM public.interviews AS i
    JOIN public.applications AS a ON a.id = i.application_id
    JOIN public.jobs AS j ON j.id = a.job_id
    WHERE i.status = 'SCHEDULED' AND i.scheduled_at < p_end_at
      AND (j.company_id = p_company_id OR a.applicant_id = p_applicant_id);
$$;

-- Thêm lịch sau khi Python đã kiểm tra quyền, thời gian và lịch trùng.
-- Đầu vào: application_id, round_number, scheduled_at, duration_minutes, mode, location_or_url.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_interview(p_application_id uuid,
    p_round_number integer,
    p_scheduled_at timestamptz,
    p_duration_minutes integer,
    p_mode text,
    p_location_or_url text)
RETURNS SETOF public.interviews
LANGUAGE sql
AS $$
INSERT INTO public.interviews (id, application_id, round_number, scheduled_at, duration_minutes, mode, location_or_url)
    VALUES (gen_random_uuid(), p_application_id, p_round_number, p_scheduled_at, p_duration_minutes, p_mode, p_location_or_url)
    RETURNING *;
$$;

-- Lưu hủy lịch hoặc kết quả interview sau kiểm tra ở Python.
-- Đầu vào: id, status, result, feedback.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_interview_result(p_id uuid,
    p_status text,
    p_result text,
    p_feedback text)
RETURNS SETOF public.interviews
LANGUAGE sql
AS $$
UPDATE public.interviews
    SET status = p_status,
        result = p_result,
        feedback = p_feedback
    WHERE id = p_id
    RETURNING *;
$$;

-- Hủy lịch còn chờ khi application bị withdraw/reject.
-- Đầu vào: application_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.cancel_application_interviews(p_application_id uuid)
RETURNS void
LANGUAGE sql
AS $$
UPDATE public.interviews SET status = 'CANCELLED' WHERE application_id = p_application_id AND status = 'SCHEDULED';
$$;
