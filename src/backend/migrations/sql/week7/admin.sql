-- Admin xem tài khoản qua DTO không có password_hash hoặc token; có filter/search.
CREATE OR REPLACE FUNCTION public.list_admin_users(p_keyword text,p_status text,p_role text,p_limit integer,p_offset integer)
RETURNS TABLE(id uuid,email text,full_name text,role text,status text,created_at timestamptz)
LANGUAGE sql STABLE AS $$
 SELECT u.id,u.email::text,u.full_name::text,u.role::text,u.status::text,u.created_at
 FROM public.users u WHERE (p_keyword IS NULL OR u.email ILIKE '%'||p_keyword||'%' OR u.full_name ILIKE '%'||p_keyword||'%')
 AND (p_status IS NULL OR u.status=p_status) AND (p_role IS NULL OR u.role=p_role)
 ORDER BY u.created_at,u.id LIMIT p_limit OFFSET p_offset;
$$;

-- Serialize thay đổi tài khoản admin để không khóa admin active cuối cùng.
CREATE OR REPLACE FUNCTION public.lock_admin_moderation()
RETURNS void LANGUAGE sql AS $$ SELECT pg_advisory_xact_lock(806002); $$;

-- Đếm admin active để Python bảo vệ admin cuối cùng.
CREATE OR REPLACE FUNCTION public.count_active_admins()
RETURNS TABLE(total bigint) LANGUAGE sql STABLE AS $$
 SELECT count(*) FROM public.users WHERE role='ADMIN' AND status='ACTIVE';
$$;

-- Lưu trạng thái user; quyền, self-lock và admin cuối cùng được Python kiểm tra.
CREATE OR REPLACE FUNCTION public.set_user_status(p_id uuid,p_status text)
RETURNS TABLE(id uuid,email text,full_name text,role text,status text,created_at timestamptz)
LANGUAGE sql AS $$
 UPDATE public.users u SET status=p_status,updated_at=now() WHERE u.id=p_id
 RETURNING u.id,u.email::text,u.full_name::text,u.role::text,u.status::text,u.created_at;
$$;

-- Thu hồi mọi phiên khi suspend user; khôi phục trạng thái không phục hồi token cũ.
CREATE OR REPLACE FUNCTION public.revoke_user_sessions(p_user_id uuid)
RETURNS void LANGUAGE sql AS $$
 UPDATE public.auth_sessions SET revoked_at=COALESCE(revoked_at,now()) WHERE user_id=p_user_id;
$$;

-- Admin khóa/mở company; các public API và quyền recruiter kiểm tra status này.
CREATE OR REPLACE FUNCTION public.set_company_status(p_id uuid,p_status text)
RETURNS SETOF public.companies LANGUAGE sql AS $$
 UPDATE public.companies SET status=p_status,updated_at=now() WHERE id=p_id RETURNING *;
$$;

-- Admin đọc audit tối thiểu, không chứa credentials/file contents.
CREATE OR REPLACE FUNCTION public.list_admin_audit(p_limit integer,p_offset integer)
RETURNS SETOF public.audit_logs LANGUAGE sql STABLE AS $$
 SELECT * FROM public.audit_logs ORDER BY created_at DESC,id LIMIT p_limit OFFSET p_offset;
$$;
