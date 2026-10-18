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
