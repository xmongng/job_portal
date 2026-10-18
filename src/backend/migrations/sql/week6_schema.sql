-- Schema changes for Weeks 4–6. This migration snapshot is immutable.
ALTER TABLE public.jobs DROP CONSTRAINT ck_jobs_valid_status;
ALTER TABLE public.jobs ADD CONSTRAINT ck_jobs_valid_status CHECK (status IN ('DRAFT','PENDING_APPROVAL','PUBLISHED','REJECTED','CLOSED'));
ALTER TABLE public.jobs ADD CONSTRAINT ck_jobs_nonnegative_salary_max CHECK (salary_max IS NULL OR salary_max>=0);
ALTER TABLE public.applications DROP CONSTRAINT ck_applications_valid_status;
ALTER TABLE public.applications ADD CONSTRAINT ck_applications_valid_status CHECK (status IN ('APPLIED','SCREENING','INTERVIEW','OFFER','HIRED','REJECTED','WITHDRAWN'));
ALTER TABLE public.applications ADD COLUMN resume_snapshot jsonb;
-- Existing applications retain their metadata; their original private file key is preserved.
UPDATE public.applications a SET resume_snapshot=jsonb_build_object('title',r.title,'original_name',r.original_name,'mime_type',r.mime_type,'size_bytes',r.size_bytes,'storage_key',r.storage_key)
FROM public.resumes r WHERE r.id=a.resume_id;
ALTER TABLE public.interviews ADD COLUMN duration_minutes integer NOT NULL DEFAULT 60;
ALTER TABLE public.interviews ADD CONSTRAINT ck_interviews_valid_duration CHECK (duration_minutes BETWEEN 15 AND 480);
ALTER TABLE public.offers DROP CONSTRAINT ck_offers_valid_status;
ALTER TABLE public.offers ADD CONSTRAINT ck_offers_valid_status CHECK (status IN ('DRAFT','SENT','ACCEPTED','REJECTED','EXPIRED','CANCELLED'));
ALTER TABLE public.offers DROP CONSTRAINT uq_offers_application_id;
CREATE UNIQUE INDEX uq_offer_active_application ON public.offers(application_id) WHERE status IN ('DRAFT','SENT','ACCEPTED');
-- Normalize legacy multiple defaults deterministically before adding the invariant.
WITH ranked AS (SELECT id,row_number() OVER (PARTITION BY applicant_id ORDER BY created_at,id) AS rn FROM public.resumes WHERE is_default)
UPDATE public.resumes SET is_default=false FROM ranked WHERE public.resumes.id=ranked.id AND ranked.rn>1;
CREATE UNIQUE INDEX uq_resume_default_applicant ON public.resumes(applicant_id) WHERE is_default;
CREATE TABLE public.job_status_history (
    id uuid PRIMARY KEY, job_id uuid NOT NULL REFERENCES public.jobs(id), actor_id uuid NOT NULL REFERENCES public.users(id),
    from_status text, to_status text NOT NULL, note text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_job_history_job ON public.job_status_history(job_id,created_at);
CREATE TABLE public.application_status_history (
    id uuid PRIMARY KEY, application_id uuid NOT NULL REFERENCES public.applications(id), actor_id uuid NOT NULL REFERENCES public.users(id),
    from_status text, to_status text NOT NULL, note text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_application_history_application ON public.application_status_history(application_id,created_at);
CREATE TABLE public.audit_logs (
    id uuid PRIMARY KEY, actor_id uuid NOT NULL REFERENCES public.users(id), action text NOT NULL,
    resource_id uuid NOT NULL, details jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_notifications_user_created ON public.notifications(user_id,created_at);
CREATE INDEX ix_applications_job_status ON public.applications(job_id,status);

ALTER TABLE public.notifications ADD COLUMN email_sent_at timestamptz;
ALTER TABLE public.notifications ADD COLUMN email_attempts integer NOT NULL DEFAULT 0;
ALTER TABLE public.notifications ADD COLUMN email_error text;
