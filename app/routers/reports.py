from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import IDCardReport, User, ReportStatus
from app.schemas import ReportCreate, ReportOut
from app.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = IDCardReport(
        reporter_id=current_user.id,
        card_owner_reg_no=payload.card_owner_reg_no,
        status=payload.status,
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
