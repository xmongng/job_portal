-- Store cho API GET /api/jobs: lấy danh sách job công khai.
-- Nhận phân trang và bộ lọc keyword/location; trả id, title và company_name.
-- Chỉ lấy job PUBLISHED, còn hạn, thuộc công ty ACTIVE và VERIFIED.
-- Trả tối đa 20 job mới nhất; không có job phù hợp thì trả 0 dòng.
-- Xóa signature cũ để tránh overload khi gọi với tham số mặc định.
DROP FUNCTION IF EXISTS public.list_public_jobs(integer, integer);
DROP FUNCTION IF EXISTS public.list_public_jobs();

-- Lấy job công khai còn hạn theo filter và phân trang; chỉ đọc dữ liệu.
Create or Replace function public.list_public_jobs(
    p_limit integer default 20,
    p_offset integer default 0,
    p_keyword text default null,
    p_location text default null
)
Returns table(
    id uuid,
    title text,
    company_name text
)
Language sql
Stable
As $$
    Select j.id, j.title::text, c.name::text
    from public.jobs as j
    Join public.companies as c on j.company_id = c.id
    Where j.status = 'PUBLISHED'
        And j.deadline > now()
        And c.status = 'ACTIVE'
        And c.verification_status = 'VERIFIED'
        And (
            p_keyword is null
            or j.title Ilike '%' || p_keyword || '%'
        )
        AND (
            p_location IS NULL
            OR j.location ILIKE '%' || p_location || '%'
        )
    order by j.created_at desc, j.id
    Limit p_limit
    Offset p_offset;
$$;


-- Lấy chi tiết job công khai theo ID.
-- Trả 0 dòng nếu job không tồn tại hoặc không đủ điều kiện công khai.
Create or Replace function public.get_public_job(p_job_id uuid)
Returns table(
    id uuid,
    title text,
    company_name text,
    description text,
    requirements text,
    location_name text,
    employment_type text,
    salary_min numeric,
    salary_max numeric,
    deadline timestamptz
)
Language sql
Stable
As $$
    Select j.id, j.title::text, c.name::text, j.description,
    j.requirements, j.location::text, j.employment_type::text,
    j.salary_min, j.salary_max, j.deadline

    from public.jobs as j
    Join public.companies as c on j.company_id = c.id
    Where j.id = p_job_id
        And j.status = 'PUBLISHED'
        And j.deadline > now()
        And c.status = 'ACTIVE'
        And c.verification_status = 'VERIFIED';
$$;

-- Lấy jobs theo ID để Python kiểm tra quyền và dữ liệu.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_job_by_id(p_id uuid)
RETURNS SETOF public.jobs
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.jobs AS t
    WHERE t.id = p_id;
$$;

-- Lấy và khóa dòng jobs tới cuối transaction, tránh cập nhật đồng thời.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_job(p_id uuid)
RETURNS SETOF public.jobs
LANGUAGE sql
AS $$
SELECT t.* FROM public.jobs AS t
    WHERE t.id = p_id
    FOR UPDATE;
$$;

-- Tạo job DRAFT; company/created_by được service lấy từ quyền hiện tại.
-- Đầu vào: company_id, created_by, title, description, requirements, location, category, employment_type, salary_min, salary_max, deadline.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_job(p_company_id uuid,
    p_created_by uuid,
    p_title text,
    p_description text,
    p_requirements text,
    p_location text,
    p_category text,
    p_employment_type text,
    p_salary_min numeric,
    p_salary_max numeric,
    p_deadline timestamptz)
RETURNS SETOF public.jobs
LANGUAGE sql
AS $$
INSERT INTO public.jobs (id, company_id, created_by, title, description, requirements, location, category, employment_type, salary_min, salary_max, deadline)
    VALUES (gen_random_uuid(), p_company_id, p_created_by, p_title, p_description, p_requirements, p_location, p_category, p_employment_type, p_salary_min, p_salary_max, p_deadline)
    RETURNING *;
$$;

-- Cập nhật nội dung job DRAFT/REJECTED sau kiểm tra ở Python.
-- Đầu vào: id, title, description, requirements, location, category, employment_type, salary_min, salary_max, deadline.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.update_job_details(p_id uuid,
    p_title text,
    p_description text,
    p_requirements text,
    p_location text,
    p_category text,
    p_employment_type text,
    p_salary_min numeric,
    p_salary_max numeric,
    p_deadline timestamptz)
RETURNS SETOF public.jobs
LANGUAGE sql
AS $$
UPDATE public.jobs
    SET title = p_title,
        description = p_description,
        requirements = p_requirements,
        location = p_location,
        category = p_category,
        employment_type = p_employment_type,
        salary_min = p_salary_min,
        salary_max = p_salary_max,
        deadline = p_deadline,
        updated_at = now()
    WHERE id = p_id
    RETURNING *;
$$;

-- Lưu trạng thái job đã đi qua state machine trong Python.
-- Đầu vào: id, status.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_job_status(p_id uuid,
    p_status text)
RETURNS SETOF public.jobs
LANGUAGE sql
AS $$
UPDATE public.jobs
    SET status = p_status,
        updated_at = now()
    WHERE id = p_id
    RETURNING *;
$$;

-- Danh sách job nội bộ của một company đã xác minh quyền.
-- Đầu vào: company_id, limit, offset.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_company_managed_jobs(p_company_id uuid,
    p_limit integer,
    p_offset integer)
RETURNS SETOF public.jobs
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.jobs AS t
    WHERE t.company_id = p_company_id
    ORDER BY t.created_at DESC, t.id
    LIMIT p_limit OFFSET p_offset;
$$;

-- Danh sách job chờ admin duyệt.
-- Đầu vào: limit, offset.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_pending_jobs(p_limit integer,
    p_offset integer)
RETURNS SETOF public.jobs
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.jobs AS t
    WHERE t.status = 'PENDING_APPROVAL'
    ORDER BY t.created_at DESC, t.id
    LIMIT p_limit OFFSET p_offset;
$$;

-- Thay danh sách skills trong cùng transaction cập nhật job.
-- Đầu vào: job_id, skill_ids.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.replace_job_skills(p_job_id uuid,
    p_skill_ids uuid[])
RETURNS void
LANGUAGE sql
AS $$
DELETE FROM public.job_skills WHERE job_id = p_job_id;
    INSERT INTO public.job_skills(job_id, skill_id)
    SELECT p_job_id, skill_id FROM unnest(p_skill_ids) AS skill_id;
$$;

-- Đọc skills của một job.
-- Đầu vào: job_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_job_skills(p_job_id uuid)
RETURNS SETOF public.skills
LANGUAGE sql STABLE
AS $$
SELECT s.* FROM public.skills AS s
    JOIN public.job_skills AS js ON js.skill_id = s.id
    WHERE js.job_id = p_job_id ORDER BY s.name, s.id;
$$;

-- Ghi lịch sử trạng thái trong cùng transaction cập nhật job.
-- Đầu vào: job_id, actor_id, from_status, to_status, note.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_job_history(p_job_id uuid,
    p_actor_id uuid,
    p_from_status text,
    p_to_status text,
    p_note text)
RETURNS SETOF public.job_status_history
LANGUAGE sql
AS $$
INSERT INTO public.job_status_history (id, job_id, actor_id, from_status, to_status, note)
    VALUES (gen_random_uuid(), p_job_id, p_actor_id, p_from_status, p_to_status, p_note)
    RETURNING *;
$$;

-- Đọc lịch sử trạng thái job theo thứ tự thời gian.
-- Đầu vào: job_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_job_history(p_job_id uuid)
RETURNS SETOF public.job_status_history
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.job_status_history AS t
    WHERE t.job_id = p_job_id
    ORDER BY t.created_at, t.id;
$$;
