from fastapi import FastAPI
from app.routers import auth, reports, passes
app = FastAPI(
    title="MUST Exam Entry Verification System",
    description="Advance exam-entry verification for students with ID card issues. Includes a supporting lost/forgotten ID reporting feature."
)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(passes.router)
@app.get("/health")
def health():
    return {"status": "ok"}
