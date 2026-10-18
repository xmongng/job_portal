from fastapi import FastAPI
from sqlalchemy.exc import DBAPIError

from app.api.errors import database_error_handler
from app.api.routes.applicant import router as applicants_router
from app.api.routes.application import router as applications_router
from app.api.routes.auth import router as auth_router
from app.api.routes.company import router as companies_router
from app.api.routes.job import router as jobs_router
from app.api.routes.pipeline import router as pipeline_router
from app.api.routes.recruitment import router as recruitment_router
from app.api.routes.resume import router as resumes_router
from app.api.routes.skill import router as skills_router

app = FastAPI(title="Job Portal API")
app.add_exception_handler(DBAPIError, database_error_handler)
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
