

-- Lấy resumes theo ID để Python kiểm tra quyền và dữ liệu.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_resume_by_id(p_id uuid)
RETURNS SETOF public.resumes
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.resumes AS t
    WHERE t.id = p_id;
$$;

-- Lấy và khóa dòng resumes tới cuối transaction, tránh cập nhật đồng thời.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.lock_resume(p_id uuid)
RETURNS SETOF public.resumes
LANGUAGE sql
AS $$
SELECT t.* FROM public.resumes AS t
    WHERE t.id = p_id
    FOR UPDATE;
$$;

-- Thêm metadata CV sau khi Python xác minh PDF và lưu file private.
-- Đầu vào: applicant_id, title, storage_key, original_name, mime_type, size_bytes, is_default.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_resume(p_applicant_id uuid,
    p_title text,
    p_storage_key text,
    p_original_name text,
    p_mime_type text,
    p_size_bytes bigint,
    p_is_default boolean)
RETURNS SETOF public.resumes
LANGUAGE sql
AS $$
INSERT INTO public.resumes (id, applicant_id, title, storage_key, original_name, mime_type, size_bytes, is_default)
    VALUES (gen_random_uuid(), p_applicant_id, p_title, p_storage_key, p_original_name, p_mime_type, p_size_bytes, p_is_default)
    RETURNING *;
$$;

-- Danh sách metadata CV của applicant đã được xác minh chính chủ.
-- Đầu vào: applicant_id, limit, offset.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_applicant_resumes(p_applicant_id uuid,
    p_limit integer,
    p_offset integer)
RETURNS SETOF public.resumes
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.resumes AS t
    WHERE t.applicant_id = p_applicant_id
    ORDER BY t.created_at DESC, t.id
    LIMIT p_limit OFFSET p_offset;
$$;

-- Lấy CV đầu tiên để xác định hoặc chọn lại default.
-- Đầu vào: applicant_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.get_first_resume(p_applicant_id uuid)
RETURNS SETOF public.resumes
LANGUAGE sql STABLE
AS $$
SELECT r.* FROM public.resumes AS r WHERE r.applicant_id = p_applicant_id
    ORDER BY r.created_at, r.id LIMIT 1;
$$;

-- Bỏ default cũ trước khi đặt default mới, sau khi Python khóa applicant.
-- Đầu vào: applicant_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.clear_default_resumes(p_applicant_id uuid)
RETURNS void
LANGUAGE sql
AS $$
UPDATE public.resumes SET is_default = false WHERE applicant_id = p_applicant_id AND is_default;
$$;

-- Đặt hoặc bỏ default trên một CV đã được xác minh chính chủ.
-- Đầu vào: id, is_default.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.set_resume_default(p_id uuid,
    p_is_default boolean)
RETURNS SETOF public.resumes
LANGUAGE sql
AS $$
UPDATE public.resumes
    SET is_default = p_is_default
    WHERE id = p_id
    RETURNING *;
$$;

-- Xóa metadata CV sau kiểm tra tham chiếu và quyền; file do Python xử lý.
-- Đầu vào: id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.delete_resume_metadata(p_id uuid)
RETURNS void
LANGUAGE sql
AS $$
DELETE FROM public.resumes WHERE id = p_id;
$$;

-- Tìm đơn tham chiếu CV để service chặn xóa CV đã sử dụng.
-- Đầu vào: resume_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.find_resume_application(p_resume_id uuid)
RETURNS SETOF public.applications
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.applications AS t
    WHERE t.resume_id = p_resume_id;
$$;
