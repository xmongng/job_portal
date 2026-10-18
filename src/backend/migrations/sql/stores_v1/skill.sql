-- Danh mục kỹ năng public, có phân trang.
CREATE OR REPLACE FUNCTION public.list_skills(p_limit integer, p_offset integer)
RETURNS TABLE(id uuid, name text)
LANGUAGE sql STABLE
AS $$
    SELECT s.id, s.name::text
    FROM public.skills AS s
    ORDER BY s.name, s.id
    LIMIT p_limit OFFSET p_offset;
$$;

-- Lấy skills theo applicant ID mà backend đã xác minh là chính chủ.
CREATE OR REPLACE FUNCTION public.get_applicant_skills(p_applicant_id uuid)
RETURNS TABLE(id uuid, name text)
LANGUAGE sql STABLE
AS $$
    SELECT s.id, s.name::text
    FROM public.skills AS s
    JOIN public.applicant_skills AS a ON a.skill_id = s.id
    WHERE a.applicant_id = p_applicant_id
    ORDER BY s.name, s.id;
$$;

-- Lấy danh mục theo các UUID để service từ chối ID không tồn tại.
-- Đầu vào: ids.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_skills_by_ids(p_ids uuid[])
RETURNS SETOF public.skills
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.skills AS t
    WHERE t.id = ANY(p_ids);
$$;

-- Admin thêm một skill vào danh mục; unique name do database bảo vệ.
-- Đầu vào: name.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_skill(p_name text)
RETURNS SETOF public.skills
LANGUAGE sql
AS $$
INSERT INTO public.skills (id, name)
    VALUES (gen_random_uuid(), p_name)
    RETURNING *;
$$;

-- Thay toàn bộ skills của applicant đã được Python khóa và xác minh.
-- Đầu vào: applicant_id, skill_ids.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.replace_applicant_skills(p_applicant_id uuid,
    p_skill_ids uuid[])
RETURNS void
LANGUAGE sql
AS $$
DELETE FROM public.applicant_skills WHERE applicant_id = p_applicant_id;
    INSERT INTO public.applicant_skills(applicant_id, skill_id)
    SELECT p_applicant_id, skill_id FROM unnest(p_skill_ids) AS skill_id;
$$;
