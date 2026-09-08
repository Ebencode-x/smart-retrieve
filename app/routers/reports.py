from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from io import BytesIO
from app.database import get_db
from app.models import IDCardReport, User, ReportStatus, Exam
from app.schemas import ReportCreate, ReportOut
from app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/reports", tags=["reports"])
STAFF = ("gate_security", "invigilator", "admin")

def compute_tier(exam: Exam) -> int:
    exam_datetime = datetime.combine(exam.exam_date, exam.exam_time)
    hours_until_exam = (exam_datetime - datetime.utcnow()).total_seconds() / 3600
    if hours_until_exam >= 48:
        return 1
    elif hours_until_exam >= 24:
        return 2
    else:
        return 3

@router.post("/", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.declaration_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm the declaration before submitting a report.",
        )
    exam = db.query(Exam).filter(Exam.id == payload.exam_id).first()
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    report = IDCardReport(
        reporter_id=current_user.id,
        exam_id=payload.exam_id,
        card_owner_reg_no=payload.card_owner_reg_no,
        status=payload.status,
        report_type=payload.report_type,
        declaration_confirmed=payload.declaration_confirmed,
        tier=compute_tier(exam),
        location=payload.location,
        description=payload.description,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/", response_model=list[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(IDCardReport)
        .filter(IDCardReport.status != ReportStatus.resolved)
        .order_by(IDCardReport.created_at.desc())
        .all()
    )

@router.patch("/{report_id}/resolve", response_model=ReportOut)
def resolve_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(IDCardReport).filter(IDCardReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.reporter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to resolve this report",
        )
    report.status = ReportStatus.resolved
    report.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    return report

@router.get("/history/{registration_number:path}", response_model=list[ReportOut])
def report_history(
    registration_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*STAFF)),
):
    return (
        db.query(IDCardReport)
        .filter(IDCardReport.card_owner_reg_no == registration_number)
        .order_by(IDCardReport.created_at.desc())
        .all()
    )

def _exception_list_query(db: Session, exam_id: int):
    """Printed list for gate guards: Tier 1/2 pre-registered reports only.
    Tier 3 (same-day/emergency) is deliberately excluded here — those students
    are routed to the invigilator inside the room for real-time verification."""
    return (
        db.query(IDCardReport)
        .filter(
            IDCardReport.exam_id == exam_id,
            IDCardReport.status != ReportStatus.resolved,
            IDCardReport.tier.in_([1, 2]),
        )
        .order_by(IDCardReport.card_owner_reg_no)
        .all()
    )

@router.get("/exception-list/{exam_id}", response_model=list[ReportOut])
def exception_list(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*STAFF)),
):
    return _exception_list_query(db, exam_id)

@router.get("/exception-list/{exam_id}/pdf")
def exception_list_pdf(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("gate_security", "admin")),
):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    reports = _exception_list_query(db, exam_id)

    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "MUST Exam Entry Verification System")
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Exception List — {exam.course_code} | Room {exam.room} | {exam.exam_date} {exam.exam_time}")
    y -= 30

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Reg. Number")
    c.drawString(200, y, "Report Type")
    c.drawString(320, y, "Tier")
    c.drawString(370, y, "Status")
    y -= 15
    c.line(50, y, 545, y)
    y -= 15

    c.setFont("Helvetica", 10)
    for r in reports:
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
        c.drawString(50, y, r.card_owner_reg_no)
        c.drawString(200, y, r.report_type.value)
        c.drawString(320, y, str(r.tier))
        c.drawString(370, y, r.status.value)
        y -= 18

    if not reports:
        c.drawString(50, y, "No pre-registered exception reports for this exam.")

    c.save()
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=exception_list_exam_{exam_id}.pdf"},
    )

@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    report = db.query(IDCardReport).filter(IDCardReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        db.delete(report)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete this report — a clearance pass is linked to it",
        )
