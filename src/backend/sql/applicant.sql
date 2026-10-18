-- Lấy hồ sơ applicant theo user ID đã được API xác minh từ JWT.
CREATE OR REPLACE FUNCTION public.get_applicant_profile(p_user_id uuid)
RETURNS TABLE (
    id uuid,
    user_id uuid,
    headline varchar,
    summary text,
    location varchar,
    education jsonb,
    experience jsonb,
    desired_salary numeric
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        a.id,
        a.user_id,
        a.headline,
        a.summary,
        a.location,
        a.education,
        a.experience,
        a.desired_salary
    FROM public.applicants AS a
    WHERE a.user_id = p_user_id;
$$;


-- Tạo hoặc thay hồ sơ chính chủ; nếu đã có user_id thì cập nhật cùng dòng.
Create or Replace function public.upsert_applicant_profile(
    p_user_id uuid,
    p_headline varchar,
    p_summary text,
    p_location varchar,
    p_education jsonb,
    p_experience jsonb,
    p_desired_salary numeric
)
RETURNS SETOF public.applicants
Language sql
As $$
    insert into public.applicants as a(
        id, user_id, headline, summary, location, education, experience, desired_salary
    )
    values(
        gen_random_uuid(),
        p_user_id,
        p_headline,
        p_summary,
        p_location,
        p_education,
        p_experience,
        p_desired_salary
    )
    on conflict (user_id) do update set
    headline = p_headline,
    summary = p_summary,
    location = p_location,
    education = p_education,
    experience = p_experience,
    desired_salary = p_desired_salary,
    updated_at = now()
    RETURNING a.*;

$$;

-- Lấy hồ sơ applicant để xác định user sở hữu.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_applicant_by_id(p_id uuid)
RETURNS SETOF public.applicants
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.applicants AS t
    WHERE t.id = p_id;
$$;

-- Lấy hồ sơ theo user trong JWT.
-- Đầu vào: user_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_applicant_by_user(p_user_id uuid)
RETURNS SETOF public.applicants
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.applicants AS t
    WHERE t.user_id = p_user_id;
$$;

-- Khóa hồ sơ khi thay skills hoặc default CV.
-- Đầu vào: user_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_applicant_by_user(p_user_id uuid)
RETURNS SETOF public.applicants
LANGUAGE sql
AS $$
SELECT t.* FROM public.applicants AS t
    WHERE t.user_id = p_user_id
    FOR UPDATE;
$$;
