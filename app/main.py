from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.routers import auth, reports, passes, exams, users
from app.database import get_db

app = FastAPI(
    title="MUST Exam Entry Verification System",
    description="Advance exam-entry verification for students with ID card issues. Includes a supporting lost/forgotten ID reporting feature."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smart-temporary-exam-ver.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(exams.router)
app.include_router(reports.router)
app.include_router(passes.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Touches the DB (not just the app) so a keep-alive ping also stops
    the Supabase free-tier project from auto-pausing due to inactivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        return {"status": "ok", "db": "unreachable"}

@app.get("/")
def page_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/register")
def page_register(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/dashboard")
def page_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get("/report")
def page_report(request: Request):
    return templates.TemplateResponse(request=request, name="report.html")

@app.get("/exams")
def page_exams(request: Request):
    return templates.TemplateResponse(request=request, name="exams.html")

@app.get("/exception-list")
def page_exception_list(request: Request):
    return templates.TemplateResponse(request=request, name="exception_list.html")

@app.get("/clearance-pass")
def page_clearance_pass(request: Request):
    return templates.TemplateResponse(request=request, name="clearance_pass.html")
