from fastapi import FastAPI

app = FastAPI(title="Job Portal API")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Add routers here as each business feature is implemented.
