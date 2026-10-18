

-- Ghi audit cùng transaction nghiệp vụ; details dùng giá trị mặc định schema.
-- Đầu vào: actor_id, action, resource_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_audit_log(p_actor_id uuid,
    p_action text,
    p_resource_id uuid)
RETURNS SETOF public.audit_logs
LANGUAGE sql
AS $$
INSERT INTO public.audit_logs (id, actor_id, action, resource_id)
    VALUES (gen_random_uuid(), p_actor_id, p_action, p_resource_id)
    RETURNING *;
$$;

-- Ghi thông báo in-app trong cùng transaction nghiệp vụ.
-- Đầu vào: user_id, title, body, resource_type, resource_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.insert_notification(p_user_id uuid,
    p_title text,
    p_body text,
    p_resource_type text,
    p_resource_id uuid)
RETURNS SETOF public.notifications
LANGUAGE sql
AS $$
INSERT INTO public.notifications (id, user_id, title, body, resource_type, resource_id)
    VALUES (gen_random_uuid(), p_user_id, p_title, p_body, p_resource_type, p_resource_id)
    RETURNING *;
$$;

-- Đọc thông báo chính chủ có phân trang; DTO loại trường xử lý email nội bộ.
-- Đầu vào: user_id, limit, offset.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.list_user_notifications(p_user_id uuid,
    p_limit integer,
    p_offset integer)
RETURNS SETOF public.notifications
LANGUAGE sql STABLE
AS $$
SELECT t.* FROM public.notifications AS t
    WHERE t.user_id = p_user_id
    ORDER BY t.created_at DESC, t.id
    LIMIT p_limit OFFSET p_offset;
$$;

-- Đánh dấu đã đọc đúng chủ sở hữu; gọi lặp lại giữ nguyên read_at.
-- Đầu vào: id, user_id.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.mark_notification_read(p_id uuid,
    p_user_id uuid)
RETURNS SETOF public.notifications
LANGUAGE sql
AS $$
UPDATE public.notifications SET read_at = COALESCE(read_at, now())
    WHERE id = p_id AND user_id = p_user_id RETURNING *;
$$;

-- Worker lấy và khóa thông báo đã commit để gửi SMTP; bỏ qua row worker khác đang xử lý.
-- Đầu vào: limit.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.claim_notification_emails(p_limit integer)
RETURNS TABLE(id uuid, title text, body text, email text)
LANGUAGE sql
AS $$
SELECT n.id, n.title::text, n.body::text, u.email::text
    FROM public.notifications AS n JOIN public.users AS u ON u.id = n.user_id
    WHERE n.email_sent_at IS NULL AND n.email_attempts < 5
    ORDER BY n.created_at, n.id LIMIT p_limit
    FOR UPDATE OF n SKIP LOCKED;
$$;

-- Lưu kết quả gửi email; lỗi SMTP không tác động transaction tuyển dụng đã commit.
-- Đầu vào: id, error.
-- Transaction do Python quản lý; function không tự COMMIT.
CREATE OR REPLACE FUNCTION public.record_notification_email_attempt(p_id uuid,
    p_error text)
RETURNS void
LANGUAGE sql
AS $$
UPDATE public.notifications
    SET email_attempts = email_attempts + 1, email_error = p_error,
        email_sent_at = CASE WHEN p_error IS NULL THEN now() ELSE NULL END
    WHERE id = p_id;
$$;
