-- Store cho API GET /api/jobs: lấy danh sách job công khai.
-- Không nhận tham số; trả các cột id, title và company_name.
-- Chỉ lấy job PUBLISHED, còn hạn, thuộc công ty ACTIVE và VERIFIED.
-- Trả tối đa 20 job mới nhất; không có job phù hợp thì trả 0 dòng.
Create or Replace function public.list_public_jobs(
    p_limit integer default 20,
    p_offset integer default 0
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