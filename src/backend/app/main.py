from fastapi import FastAPI

from app.api.routes.company import router as companies_router

app = FastAPI(title="Job Portal API")
app.include_router(companies_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}