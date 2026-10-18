-- Viết các stored function/procedure liên quan đến company bên dưới.
-- Chạy SQL trên PostgreSQL để tạo hoặc cập nhật store trong database.

-- Lấy tối đa 20 công ty đã xác minh và đang hoạt động, sắp xếp theo tên và ID.
CREATE OR REPLACE FUNCTION public.list_public_companies()
RETURNS TABLE (
    id uuid,
    name text,
    industry text,
    location_name text
)
Language SQL
Stable
As $$
    Select c.id, c.name::text, c.industry::text, c.location::text
    From public.companies c
    Where c.verification_status = 'VERIFIED'
    and c.status = 'ACTIVE'
    order by c.name, c.id
    limit 20;
$$;




-- Lấy chi tiết công ty công khai theo ID; trả 0 dòng nếu không tồn tại hoặc không công khai.
Create or Replace function public.get_public_company(p_company_id uuid)
Returns table(
    id uuid,
    name text,
    description text,
    industry text,
    location_name text,
    website_url text
)
Language SQL
As $$
    Select c.id, c.name::text, c.description::text,c.industry::text, 
    c.location::text, c.website_url::text
    from public.companies as c
    where c.id = p_company_id
        and c.status = 'ACTIVE'
        and c.verification_status = 'VERIFIED';
$$;



-- Lấy tối đa 20 job đã đăng và còn hạn của một công ty công khai.
CREATE OR REPLACE FUNCTION public.list_public_company_jobs(p_company_id uuid)
Returns table(
    id uuid,
    title text,
    company_name text
)
Language SQL
Stable
As $$
    Select j.id, j.title::text, c.name::text
    from public.jobs as j
    join public.companies c on j.company_id = c.id
    where c.id = p_company_id
        and c.status = 'ACTIVE'
        and c.verification_status = 'VERIFIED'
        and j.status = 'PUBLISHED'
        and j.deadline > now()
    order by j.created_at desc, j.id
    limit 20;
$$;

-- Lấy companies theo ID để Python kiểm tra quyền và dữ liệu.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_company_by_id(p_id uuid)
RETURNS SETOF public.companies
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.companies AS t
    WHERE t.id = p_id;
$$;

-- Lấy và khóa dòng companies tới cuối transaction, tránh cập nhật đồng thời.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_company(p_id uuid)
RETURNS SETOF public.companies
LANGUAGE sql
AS $$
SELECT t.* FROM public.companies AS t
    WHERE t.id = p_id
    FOR UPDATE;
$$;

-- Lấy company membership của recruiter (mỗi user tối đa một company).
-- Đầu vào: user_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_membership_by_user(p_user_id uuid)
RETURNS SETOF public.company_memberships
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.company_memberships AS t
    WHERE t.user_id = p_user_id;
$$;

-- Lấy membership cụ thể để Python kiểm tra OWNER/MEMBER.
-- Đầu vào: company_id, user_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_company_membership(p_company_id uuid,
    p_user_id uuid)
RETURNS SETOF public.company_memberships
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.company_memberships AS t
    WHERE t.company_id = p_company_id AND t.user_id = p_user_id;
$$;

-- Thêm hồ sơ company; mặc định PENDING và ACTIVE từ schema.
-- Đầu vào: name, description, industry, location, website_url.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_company(p_name text,
    p_description text,
    p_industry text,
    p_location text,
    p_website_url text)
RETURNS SETOF public.companies
LANGUAGE sql
AS $$
INSERT INTO public.companies (id, name, description, industry, location, website_url)
    VALUES (gen_random_uuid(), p_name, p_description, p_industry, p_location, p_website_url)
    RETURNING *;
$$;

-- Cập nhật hồ sơ company sau khi Python kiểm tra OWNER.
-- Đầu vào: id, name, description, industry, location, website_url, verification_status.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.update_company_details(p_id uuid,
    p_name text,
    p_description text,
    p_industry text,
    p_location text,
    p_website_url text,
    p_verification_status text)
RETURNS SETOF public.companies
LANGUAGE sql
AS $$
UPDATE public.companies
    SET name = p_name,
        description = p_description,
        industry = p_industry,
        location = p_location,
        website_url = p_website_url,
        verification_status = p_verification_status,
        updated_at = now()
    WHERE id = p_id
    RETURNING *;
$$;

-- Lưu quyết định duyệt company do admin thực hiện.
-- Đầu vào: id, verification_status.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_company_verification(p_id uuid,
    p_verification_status text)
RETURNS SETOF public.companies
LANGUAGE sql
AS $$
UPDATE public.companies
    SET verification_status = p_verification_status,
        updated_at = now()
    WHERE id = p_id
    RETURNING *;
$$;

-- Thêm OWNER/MEMBER đã được service xác minh quyền.
-- Đầu vào: company_id, user_id, membership_role.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_company_membership(p_company_id uuid,
    p_user_id uuid,
    p_membership_role text)
RETURNS SETOF public.company_memberships
LANGUAGE sql
AS $$
INSERT INTO public.company_memberships (id, company_id, user_id, membership_role)
    VALUES (gen_random_uuid(), p_company_id, p_user_id, p_membership_role)
    RETURNING *;
$$;

-- Xóa đúng một membership; Python chặn việc xóa OWNER.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.delete_company_membership(p_id uuid)
RETURNS void
LANGUAGE sql
AS $$
DELETE FROM public.company_memberships WHERE id = p_id;
$$;

-- Lấy các membership của company để gửi thông báo hoặc quản lý thành viên.
-- Đầu vào: company_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_memberships(p_company_id uuid)
RETURNS SETOF public.company_memberships
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.company_memberships AS t
    WHERE t.company_id = p_company_id
    ORDER BY t.created_at, t.id;
$$;

-- Lấy danh sách thành viên kèm tên/email sau khi service xác minh company.
-- Đầu vào: company_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_company_member_details(p_company_id uuid)
RETURNS TABLE(id uuid, company_id uuid, user_id uuid, membership_role text, created_at timestamptz, full_name text, email text)
LANGUAGE sql STABLE
AS $$
SELECT m.id, m.company_id, m.user_id, m.membership_role::text, m.created_at,
           u.full_name::text, u.email::text
    FROM public.company_memberships AS m
    JOIN public.users AS u ON u.id = m.user_id
    WHERE m.company_id = p_company_id
    ORDER BY u.full_name, u.id;
$$;

-- Danh sách company nội bộ cho admin, có phân trang.
-- Đầu vào: limit, offset.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_companies_for_admin(p_limit integer,
    p_offset integer)
RETURNS SETOF public.companies
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.companies AS t
    ORDER BY t.created_at, t.id
    LIMIT p_limit OFFSET p_offset;
$$;
