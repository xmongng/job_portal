-- Lấy user theo JWT và phiên còn hiệu lực; Python kiểm tra trạng thái tài khoản.
CREATE OR REPLACE FUNCTION public.get_session_user(p_user_id uuid, p_session_id uuid)
RETURNS TABLE(id uuid, email text, full_name text, role text, status text)
LANGUAGE sql STABLE
AS $$
    SELECT u.id, u.email::text, u.full_name::text, u.role::text, u.status::text
    FROM public.users AS u
    JOIN public.auth_sessions AS s ON s.user_id = u.id
    WHERE u.id = p_user_id
      AND s.id = p_session_id
      AND s.revoked_at IS NULL
      AND s.expires_at > now();
$$;
