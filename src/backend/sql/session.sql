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

-- Tìm và khóa phiên theo refresh-token hash để rotation chỉ thành công một lần.
-- Đầu vào: hash.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_auth_session_by_hash(p_hash text)
RETURNS SETOF public.auth_sessions
LANGUAGE sql
AS $$
SELECT t.* FROM public.auth_sessions AS t
    WHERE t.refresh_token_hash = p_hash
    FOR UPDATE;
$$;

-- Thay hash token sau khi Python kiểm tra phiên và tài khoản.
-- Đầu vào: id, refresh_token_hash.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_auth_session_hash(p_id uuid,
    p_refresh_token_hash text)
RETURNS SETOF public.auth_sessions
LANGUAGE sql
AS $$
UPDATE public.auth_sessions
    SET refresh_token_hash = p_refresh_token_hash
    WHERE id = p_id
    RETURNING *;
$$;

-- Thu hồi session; gọi lặp lại không thay đổi thời điểm đã thu hồi.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.revoke_auth_session(p_id uuid)
RETURNS void
LANGUAGE sql
AS $$
UPDATE public.auth_sessions SET revoked_at = COALESCE(revoked_at, now()) WHERE id = p_id;
$$;
