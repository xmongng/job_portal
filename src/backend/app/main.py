from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DBAPIError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.errors import database_error_handler
from app.api.middleware.security import RequestSecurityMiddleware
from app.api.routes.applicant import router as applicants_router
from app.api.routes.application import router as applications_router
from app.api.routes.auth import router as auth_router
from app.api.routes.company import router as companies_router
from app.api.routes.completion import router as completion_router
from app.api.routes.job import router as jobs_router
from app.api.routes.pipeline import router as pipeline_router
from app.api.routes.recruitment import router as recruitment_router
from app.api.routes.resume import router as resumes_router
from app.api.routes.skill import router as skills_router
from app.core.config import get_settings

app = FastAPI(title="Job Portal API")
app.add_exception_handler(DBAPIError, database_error_handler)
settings = get_settings()
app.add_middleware(RequestSecurityMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
    allow_credentials=False,
)
app.include_router(completion_router)
app.include_router(recruitment_router)
app.include_router(skills_router)
app.include_router(resumes_router)
app.include_router(applications_router)
app.include_router(pipeline_router)
app.include_router(companies_router)
app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(applicants_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
