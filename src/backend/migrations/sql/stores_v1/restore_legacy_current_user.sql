-- Chỉ dùng khi downgrade về revision c684d93ea201.
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
