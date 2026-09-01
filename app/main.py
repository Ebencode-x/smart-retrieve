from fastapi import FastAPI
from app.routers import auth, reports, passes

app = FastAPI(title="MUST Smart-Retrieve Portal")

app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(passes.router)


@app.get("/health")
def health():
    return {"status": "ok"}
