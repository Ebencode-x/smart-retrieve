from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, reports, passes, exams

app = FastAPI(
    title="MUST Exam Entry Verification System",
    description="Advance exam-entry verification for students with ID card issues. Includes a supporting lost/forgotten ID reporting feature."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(exams.router)
app.include_router(reports.router)
app.include_router(passes.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/health")
def health():
    return {"status": "ok"}

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
