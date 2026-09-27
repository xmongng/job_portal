from fastapi import FastAPI

from app.api.routes.job import router as jobs_router

app = FastAPI(title="Job Portal API")
app.include_router(jobs_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
