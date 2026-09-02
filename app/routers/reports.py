from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import IDCardReport, User, ReportStatus, Exam
from app.schemas import ReportCreate, ReportOut
from app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/reports", tags=["reports"])

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
            detail="Huna ruhusa ya kufunga ripoti hii",
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
    current_user: User = Depends(require_role("security")),
):
    return (
        db.query(IDCardReport)
        .filter(IDCardReport.card_owner_reg_no == registration_number)
        .order_by(IDCardReport.created_at.desc())
        .all()
    )

@router.get("/exception-list/{exam_id}", response_model=list[ReportOut])
def exception_list(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("security")),
):
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
