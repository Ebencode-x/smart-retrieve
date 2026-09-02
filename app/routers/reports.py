from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import IDCardReport, User, ReportStatus
from app.schemas import ReportCreate, ReportOut
from app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.declaration_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lazima uthibitishe tamko (declaration) kabla ya kuwasilisha ripoti.",
        )
    report = IDCardReport(
        reporter_id=current_user.id,
        card_owner_reg_no=payload.card_owner_reg_no,
        status=payload.status,
        report_type=payload.report_type,
        declaration_confirmed=payload.declaration_confirmed,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ripoti haipo")
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
