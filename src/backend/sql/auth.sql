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


-- Lấy tài khoản theo ID trong token để kiểm tra user còn tồn tại và hoạt động.
-- Không trả password_hash.
Create or Replace function public.get_current_user(p_user_id uuid)
Returns table(
    id uuid,
    email text,
    full_name text,
    role text,
    status text
)
Language sql
Stable
As $$
    Select u.id, u.email::text, u.full_name::text, u.role::text, u.status::text
    from public.users as u
    Where u.id = p_user_id;

$$;
