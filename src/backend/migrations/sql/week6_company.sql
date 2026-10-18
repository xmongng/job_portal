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
   
