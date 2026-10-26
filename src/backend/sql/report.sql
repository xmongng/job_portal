-- Tổng hợp số liệu cho admin hoặc recruiter của company đã được service xác minh.
-- company_id NULL dành cho admin toàn hệ thống.
CREATE OR REPLACE FUNCTION public.get_portal_counts(p_company_id uuid)
RETURNS TABLE(companies bigint,jobs bigint,applications bigint,interviews bigint,offers bigint)
LANGUAGE sql STABLE AS $$
 SELECT (SELECT count(*) FROM public.companies WHERE p_company_id IS NULL OR id=p_company_id),
 (SELECT count(*) FROM public.jobs WHERE p_company_id IS NULL OR company_id=p_company_id),
 (SELECT count(*) FROM public.applications a JOIN public.jobs j ON j.id=a.job_id WHERE p_company_id IS NULL OR j.company_id=p_company_id),
 (SELECT count(*) FROM public.interviews i JOIN public.applications a ON a.id=i.application_id JOIN public.jobs j ON j.id=a.job_id WHERE p_company_id IS NULL OR j.company_id=p_company_id),
 (SELECT count(*) FROM public.offers o JOIN public.applications a ON a.id=o.application_id JOIN public.jobs j ON j.id=a.job_id WHERE p_company_id IS NULL OR j.company_id=p_company_id);
$$;

-- Nhóm số job theo trạng thái, lọc đúng phạm vi company.
CREATE OR REPLACE FUNCTION public.report_job_status(p_company_id uuid)
RETURNS TABLE(status text,total bigint) LANGUAGE sql STABLE AS $$
 SELECT status::text,count(*) FROM public.jobs WHERE p_company_id IS NULL OR company_id=p_company_id GROUP BY status ORDER BY status;
$$;

-- Nhóm số application theo trạng thái, không trả thông tin cá nhân ứng viên.
CREATE OR REPLACE FUNCTION public.report_application_status(p_company_id uuid)
RETURNS TABLE(status text,total bigint) LANGUAGE sql STABLE AS $$
 SELECT a.status::text,count(*) FROM public.applications a JOIN public.jobs j ON j.id=a.job_id
 WHERE p_company_id IS NULL OR j.company_id=p_company_id GROUP BY a.status ORDER BY a.status;
$$;
