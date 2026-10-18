-- Script demo thêm một dòng users với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_users(p_id uuid,
    p_email text,
    p_password_hash text,
    p_full_name text,
    p_role text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.users (id, email, password_hash, full_name, role)
    VALUES (p_id, p_email, p_password_hash, p_full_name, p_role);
$$;

-- Script demo thêm một dòng auth_sessions với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_auth_sessions(p_id uuid,
    p_user_id uuid,
    p_refresh_token_hash text,
    p_expires_at timestamptz,
    p_revoked_at timestamptz)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.auth_sessions (id, user_id, refresh_token_hash, expires_at, revoked_at)
    VALUES (p_id, p_user_id, p_refresh_token_hash, p_expires_at, p_revoked_at);
$$;

-- Script demo thêm một dòng companies với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_companies(p_id uuid,
    p_name text,
    p_description text,
    p_industry text,
    p_location text,
    p_verification_status text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.companies (id, name, description, industry, location, verification_status)
    VALUES (p_id, p_name, p_description, p_industry, p_location, p_verification_status);
$$;

-- Script demo thêm một dòng company_memberships với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_company_memberships(p_id uuid,
    p_company_id uuid,
    p_user_id uuid,
    p_membership_role text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.company_memberships (id, company_id, user_id, membership_role)
    VALUES (p_id, p_company_id, p_user_id, p_membership_role);
$$;

-- Script demo thêm một dòng applicants với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_applicants(p_id uuid,
    p_user_id uuid,
    p_headline text,
    p_summary text,
    p_location text,
    p_education jsonb,
    p_experience jsonb,
    p_desired_salary numeric)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.applicants (id, user_id, headline, summary, location, education, experience, desired_salary)
    VALUES (p_id, p_user_id, p_headline, p_summary, p_location, p_education, p_experience, p_desired_salary);
$$;

-- Script demo thêm một dòng skills với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_skills(p_id uuid,
    p_name text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.skills (id, name)
    VALUES (p_id, p_name);
$$;

-- Script demo thêm một dòng applicant_skills với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_applicant_skills(p_applicant_id uuid,
    p_skill_id uuid)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.applicant_skills (applicant_id, skill_id)
    VALUES (p_applicant_id, p_skill_id);
$$;

-- Script demo thêm một dòng jobs với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_jobs(p_id uuid,
    p_company_id uuid,
    p_created_by uuid,
    p_title text,
    p_description text,
    p_requirements text,
    p_location text,
    p_category text,
    p_employment_type text,
    p_salary_min numeric,
    p_salary_max numeric,
    p_deadline timestamptz,
    p_status text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.jobs (id, company_id, created_by, title, description, requirements, location, category, employment_type, salary_min, salary_max, deadline, status)
    VALUES (p_id, p_company_id, p_created_by, p_title, p_description, p_requirements, p_location, p_category, p_employment_type, p_salary_min, p_salary_max, p_deadline, p_status);
$$;

-- Script demo thêm một dòng job_skills với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_job_skills(p_job_id uuid,
    p_skill_id uuid)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.job_skills (job_id, skill_id)
    VALUES (p_job_id, p_skill_id);
$$;

-- Script demo thêm một dòng resumes với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_resumes(p_id uuid,
    p_applicant_id uuid,
    p_title text,
    p_storage_key text,
    p_original_name text,
    p_mime_type text,
    p_size_bytes bigint,
    p_is_default boolean)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.resumes (id, applicant_id, title, storage_key, original_name, mime_type, size_bytes, is_default)
    VALUES (p_id, p_applicant_id, p_title, p_storage_key, p_original_name, p_mime_type, p_size_bytes, p_is_default);
$$;

-- Script demo thêm một dòng applications với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_applications(p_id uuid,
    p_job_id uuid,
    p_applicant_id uuid,
    p_resume_id uuid,
    p_cover_letter text,
    p_recruiter_note text,
    p_status text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.applications (id, job_id, applicant_id, resume_id, cover_letter, recruiter_note, status)
    VALUES (p_id, p_job_id, p_applicant_id, p_resume_id, p_cover_letter, p_recruiter_note, p_status);
$$;

-- Script demo thêm một dòng interviews với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_interviews(p_id uuid,
    p_application_id uuid,
    p_round_number bigint,
    p_scheduled_at timestamptz,
    p_mode text,
    p_location_or_url text,
    p_status text,
    p_result text,
    p_feedback text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.interviews (id, application_id, round_number, scheduled_at, mode, location_or_url, status, result, feedback)
    VALUES (p_id, p_application_id, p_round_number, p_scheduled_at, p_mode, p_location_or_url, p_status, p_result, p_feedback);
$$;

-- Script demo thêm một dòng offers với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_offers(p_id uuid,
    p_application_id uuid,
    p_salary numeric,
    p_start_date date,
    p_response_deadline timestamptz,
    p_terms text,
    p_status text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.offers (id, application_id, salary, start_date, response_deadline, terms, status)
    VALUES (p_id, p_application_id, p_salary, p_start_date, p_response_deadline, p_terms, p_status);
$$;

-- Script demo thêm một dòng notifications với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_notifications(p_id uuid,
    p_user_id uuid,
    p_title text,
    p_body text,
    p_resource_type text,
    p_resource_id uuid)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.notifications (id, user_id, title, body, resource_type, resource_id)
    VALUES (p_id, p_user_id, p_title, p_body, p_resource_type, p_resource_id);
$$;

-- Script demo thêm một dòng job_status_history với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_job_status_history(p_id uuid,
    p_job_id uuid,
    p_actor_id uuid,
    p_from_status text,
    p_to_status text,
    p_note text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.job_status_history (id, job_id, actor_id, from_status, to_status, note)
    VALUES (p_id, p_job_id, p_actor_id, p_from_status, p_to_status, p_note);
$$;

-- Script demo thêm một dòng application_status_history với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_application_status_history(p_id uuid,
    p_application_id uuid,
    p_actor_id uuid,
    p_from_status text,
    p_to_status text,
    p_note text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.application_status_history (id, application_id, actor_id, from_status, to_status, note)
    VALUES (p_id, p_application_id, p_actor_id, p_from_status, p_to_status, p_note);
$$;

-- Script demo thêm một dòng audit_logs với UUID xác định; không dùng trong API.
-- Chỉ chạy sau khi script đã kiểm tra database phát triển và các bảng trống.
CREATE OR REPLACE FUNCTION public.seed_audit_logs(p_id uuid,
    p_actor_id uuid,
    p_action text,
    p_resource_id uuid,
    p_details jsonb)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO public.audit_logs (id, actor_id, action, resource_id, details)
    VALUES (p_id, p_actor_id, p_action, p_resource_id, p_details);
$$;

-- Lấy tên database và revision để script seed kiểm tra đúng môi trường.
CREATE OR REPLACE FUNCTION public.get_seed_context()
RETURNS TABLE(database_name text, revision text)
LANGUAGE sql STABLE AS $$
    SELECT current_database()::text, version_num::text FROM public.alembic_version;
$$;

-- Đếm các bảng nghiệp vụ để script từ chối seed nếu đã có dữ liệu.
CREATE OR REPLACE FUNCTION public.get_seed_counts()
RETURNS TABLE(table_name text, row_count bigint)
LANGUAGE sql STABLE AS $$
    SELECT 'users'::text, count(*) FROM public.users
    UNION ALL
    SELECT 'auth_sessions'::text, count(*) FROM public.auth_sessions
    UNION ALL
    SELECT 'companies'::text, count(*) FROM public.companies
    UNION ALL
    SELECT 'company_memberships'::text, count(*) FROM public.company_memberships
    UNION ALL
    SELECT 'applicants'::text, count(*) FROM public.applicants
    UNION ALL
    SELECT 'skills'::text, count(*) FROM public.skills
    UNION ALL
    SELECT 'applicant_skills'::text, count(*) FROM public.applicant_skills
    UNION ALL
    SELECT 'jobs'::text, count(*) FROM public.jobs
    UNION ALL
    SELECT 'job_skills'::text, count(*) FROM public.job_skills
    UNION ALL
    SELECT 'resumes'::text, count(*) FROM public.resumes
    UNION ALL
    SELECT 'applications'::text, count(*) FROM public.applications
    UNION ALL
    SELECT 'interviews'::text, count(*) FROM public.interviews
    UNION ALL
    SELECT 'offers'::text, count(*) FROM public.offers
    UNION ALL
    SELECT 'notifications'::text, count(*) FROM public.notifications
    UNION ALL
    SELECT 'job_status_history'::text, count(*) FROM public.job_status_history
    UNION ALL
    SELECT 'application_status_history'::text, count(*) FROM public.application_status_history
    UNION ALL
    SELECT 'audit_logs'::text, count(*) FROM public.audit_logs;
$$;
