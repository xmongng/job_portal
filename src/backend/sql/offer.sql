

-- Đọc offer theo ID; Python kiểm tra draft/quyền/ngày hết hạn.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_offer_by_id(p_id uuid)
RETURNS SETOF public.offers
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.offers AS t
    WHERE t.id = p_id;
$$;

-- Đọc các offer của application, Python ẩn draft khỏi applicant.
-- Đầu vào: application_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_application_offers(p_application_id uuid)
RETURNS SETOF public.offers
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.offers AS t
    WHERE t.application_id = p_application_id
    ORDER BY t.created_at, t.id;
$$;

-- Thêm offer DRAFT; partial unique index bảo vệ một offer active/application.
-- Đầu vào: application_id, salary, start_date, response_deadline, terms.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_offer(p_application_id uuid,
    p_salary numeric,
    p_start_date date,
    p_response_deadline timestamptz,
    p_terms text)
RETURNS SETOF public.offers
LANGUAGE sql
AS $$
INSERT INTO public.offers (id, application_id, salary, start_date, response_deadline, terms)
    VALUES (gen_random_uuid(), p_application_id, p_salary, p_start_date, p_response_deadline, p_terms)
    RETURNING *;
$$;

-- Lưu trạng thái offer sau khi Python kiểm tra người gọi và deadline.
-- Đầu vào: id, status.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_offer_status(p_id uuid,
    p_status text)
RETURNS SETOF public.offers
LANGUAGE sql
AS $$
UPDATE public.offers
    SET status = p_status,
        updated_at = now()
    WHERE id = p_id
    RETURNING *;
$$;

-- Hủy các offer pending khi application bị reject/withdraw.
-- Đầu vào: application_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.cancel_application_offers(p_application_id uuid)
RETURNS void
LANGUAGE sql
AS $$
UPDATE public.offers SET status = 'CANCELLED', updated_at = now() WHERE application_id = p_application_id AND status IN ('DRAFT','SENT');
$$;
