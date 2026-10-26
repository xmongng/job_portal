-- Xếp hạng job công khai bằng skills (70), location (15), salary (15).
-- Chỉ nhận user ID từ JWT; không gửi hồ sơ cá nhân hoặc CV tới AI.
CREATE OR REPLACE FUNCTION public.recommend_jobs(p_user_id uuid, p_limit integer, p_offset integer)
RETURNS TABLE(id uuid, title text, company_name text, location text, salary_min numeric,
 salary_max numeric, skill_score integer, location_score integer, salary_score integer,
 score integer, matched_skills text[], missing_skills text[])
LANGUAGE sql STABLE AS $$
 WITH candidate AS (
   SELECT * FROM public.applicants WHERE user_id=p_user_id
 ), ranked AS (
   SELECT j.id, j.title::text, c.name::text AS company_name, j.location::text,
     j.salary_min, j.salary_max,
     CASE WHEN count(s.id)=0 THEN 0 ELSE round(70.0*count(ask.skill_id)/count(s.id))::integer END AS skill_score,
     CASE WHEN lower(trim(j.location))=lower(trim(a.location)) AND trim(a.location)<>'' THEN 15 ELSE 0 END AS location_score,
     CASE WHEN a.desired_salary IS NOT NULL AND
       (j.salary_max>=a.desired_salary OR (j.salary_max IS NULL AND j.salary_min>=a.desired_salary)) THEN 15 ELSE 0 END AS salary_score,
     COALESCE(array_agg(s.name::text ORDER BY s.name) FILTER (WHERE ask.skill_id IS NOT NULL),'{}'::text[]) AS matched_skills,
     COALESCE(array_agg(s.name::text ORDER BY s.name) FILTER (WHERE s.id IS NOT NULL AND ask.skill_id IS NULL),'{}'::text[]) AS missing_skills
   FROM public.jobs j JOIN public.companies c ON c.id=j.company_id CROSS JOIN candidate a
   LEFT JOIN public.job_skills js ON js.job_id=j.id
   LEFT JOIN public.skills s ON s.id=js.skill_id
   LEFT JOIN public.applicant_skills ask ON ask.skill_id=s.id AND ask.applicant_id=a.id
   WHERE j.status='PUBLISHED' AND j.deadline>now() AND c.status='ACTIVE' AND c.verification_status='VERIFIED'
   GROUP BY j.id,c.name,a.location,a.desired_salary
 )
 SELECT r.id,r.title,r.company_name,r.location,r.salary_min,r.salary_max,
   r.skill_score,r.location_score,r.salary_score,
   r.skill_score+r.location_score+r.salary_score AS score,r.matched_skills,r.missing_skills
 FROM ranked r ORDER BY score DESC,r.id LIMIT p_limit OFFSET p_offset;
$$;

-- Đọc facts của một job để giải thích match với công thức giống recommendation.
CREATE OR REPLACE FUNCTION public.get_job_match(p_user_id uuid,p_job_id uuid)
RETURNS TABLE(id uuid, title text, company_name text, location text, salary_min numeric,
 salary_max numeric, skill_score integer, location_score integer, salary_score integer,
 score integer, matched_skills text[], missing_skills text[])
LANGUAGE sql STABLE AS $$
 SELECT * FROM public.recommend_jobs(p_user_id,2147483647,0) WHERE id=p_job_id;
$$;
