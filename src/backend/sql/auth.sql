-- Tạo tài khoản; trả thông tin public, không trả password_hash.
Create or Replace function public.register_user(
    p_email text,
    p_password_hash text,
    p_full_name text,
    p_role text
)
Returns table(
    id uuid,
    email text,
    full_name text,
    role text,
    status text,
    created_at timestamptz
)
Language plpgsql
As $$
    Begin 
        if p_role is null
            or p_role not in ('APPLICANT', 'RECRUITER') then
            raise exception 'Invalid role';
        end if;
        Return query 
        Insert into public.users as u(id, email, password_hash, full_name,role)
        values(
            gen_random_uuid(),
            lower(trim(p_email)),
            p_password_hash,
            trim(p_full_name),
            p_role
        )
        returning
        u.id, u.email::text, u.full_name::text, u.role::text, u.status::text, u.created_at;
        
    end;
$$;


-- Lấy tài khoản theo email để backend kiểm tra đăng nhập.
CREATE OR REPLACE FUNCTION public.get_user_for_login(p_email text)
RETURNS TABLE (
    id uuid,
    email text,
    full_name text,
    role text,
    status text,
    password_hash text
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        u.id,
        u.email::text,
        u.full_name::text,
        u.role::text,
        u.status::text,
        u.password_hash
    FROM public.users AS u
    WHERE u.email = lower(trim(p_email));
$$;


-- Tạo phiên đăng nhập, chỉ lưu hash của refresh token.
-- Trả ID phiên và thời điểm hết hạn cho backend.
CREATE OR REPLACE FUNCTION public.create_auth_session(
    p_user_id uuid,
    p_refresh_token_hash text,
    p_expires_at timestamptz
)
RETURNS TABLE (
    id uuid,
    expires_at timestamptz
)
LANGUAGE sql
AS $$
    INSERT INTO public.auth_sessions AS s (
        id,
        user_id,
        refresh_token_hash,
        expires_at
    )
    VALUES (
        gen_random_uuid(),
        p_user_id,
        p_refresh_token_hash,
        p_expires_at
    )
    RETURNING s.id, s.expires_at;
$$;

-- Lấy users theo ID để Python kiểm tra quyền và dữ liệu.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_user_by_id(p_id uuid)
RETURNS SETOF public.users
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.users AS t
    WHERE t.id = p_id;
$$;

-- Lấy và khóa dòng users tới cuối transaction, tránh cập nhật đồng thời.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_user(p_id uuid)
RETURNS SETOF public.users
LANGUAGE sql
AS $$
SELECT t.* FROM public.users AS t
    WHERE t.id = p_id
    FOR UPDATE;
$$;

-- Tìm và khóa recruiter đang hoạt động theo email.
-- Đầu vào: email.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.find_active_recruiter(p_email text)
RETURNS SETOF public.users
LANGUAGE sql
AS $$
SELECT t.* FROM public.users AS t
    WHERE t.email = lower(trim(p_email)) AND t.role = 'RECRUITER' AND t.status = 'ACTIVE'
    FOR UPDATE;
$$;

-- CLI tạo admin; không có public endpoint gọi store này.
-- Đầu vào: email, password_hash, full_name, role.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_admin(p_email text,
    p_password_hash text,
    p_full_name text,
    p_role text)
RETURNS SETOF public.users
LANGUAGE sql
AS $$
INSERT INTO public.users (id, email, password_hash, full_name, role)
    VALUES (gen_random_uuid(), p_email, p_password_hash, p_full_name, p_role)
    RETURNING *;
$$;
