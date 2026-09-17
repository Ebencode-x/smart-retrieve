from datetime import datetime, timedelta
import pyotp
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ClearancePass, User, IDCardReport
from app.schemas import PassOut, PassVerify, PassGenerate
from app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/passes", tags=["passes"])
PASS_VALIDITY_MINUTES = 10


@router.get("/mine", response_model=list[PassOut])
def list_my_passes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    passes = (
        db.query(ClearancePass)
        .filter(ClearancePass.owner_id == current_user.id)
        .order_by(ClearancePass.issued_at.desc())
        .all()
    )
    return [
        PassOut(id=p.id, report_id=p.report_id, expires_at=p.expires_at, is_used=p.is_used, code="")
        for p in passes
    ]


@router.get("/", response_model=list[PassOut])
def list_all_passes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    passes = db.query(ClearancePass).order_by(ClearancePass.issued_at.desc()).all()
    return [
        PassOut(id=p.id, report_id=p.report_id, expires_at=p.expires_at, is_used=p.is_used, code="")
        for p in passes
    ]


@router.post("/generate", response_model=PassOut, status_code=201)
def generate_pass(
    payload: PassGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(IDCardReport).filter(IDCardReport.id == payload.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot generate a pass for a report that is not yours")
    if report.resolved_at is not None:
        raise HTTPException(status_code=400, detail="This report is already resolved")
    if report.tier != 3:
        raise HTTPException(
            status_code=400,
            detail="Clearance Pass is for Tier 3 only — Tier 1/2 use the printed gate list",
        )

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, interval=PASS_VALIDITY_MINUTES * 60)
    clearance_pass = ClearancePass(
        owner_id=current_user.id,
        report_id=report.id,
        totp_secret=secret,
        expires_at=datetime.utcnow() + timedelta(minutes=PASS_VALIDITY_MINUTES),
    )
    db.add(clearance_pass)
    db.commit()
    db.refresh(clearance_pass)
    return PassOut(
        id=clearance_pass.id,
        report_id=clearance_pass.report_id,
        expires_at=clearance_pass.expires_at,
        is_used=clearance_pass.is_used,
        code=totp.now(),
    )


@router.delete("/{pass_id}", status_code=204)
def void_pass(
    pass_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clearance_pass = db.query(ClearancePass).filter(ClearancePass.id == pass_id).first()
    if not clearance_pass:
        raise HTTPException(status_code=404, detail="Pass not found")
    is_owner = clearance_pass.owner_id == current_user.id
    is_admin = current_user.role.value == "admin"
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="You cannot void this pass")
    if clearance_pass.is_used:
        raise HTTPException(status_code=400, detail="A used pass cannot be voided")
    db.delete(clearance_pass)
    db.commit()


@router.post("/verify")
def verify_pass(
    payload: PassVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("invigilator", "admin")),
):
    clearance_pass = db.query(ClearancePass).filter(ClearancePass.id == payload.pass_id).first()
    if not clearance_pass:
        raise HTTPException(status_code=404, detail="Pass not found")
    if clearance_pass.is_used:
        raise HTTPException(status_code=400, detail="This pass has already been used")
    if clearance_pass.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This pass has expired")

    totp = pyotp.TOTP(clearance_pass.totp_secret, interval=PASS_VALIDITY_MINUTES * 60)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    clearance_pass.is_used = True
    clearance_pass.verified_by_id = current_user.id
    db.commit()

    report = clearance_pass.report
    exam = report.exam if report else None

    return {
        "status": "verified",
        "owner_id": clearance_pass.owner_id,
        "report_id": clearance_pass.report_id,
        "card_owner_reg_no": report.card_owner_reg_no if report else None,
        "exam": {
            "course_code": exam.course_code,
            "room": exam.room,
            "exam_date": str(exam.exam_date),
        } if exam else None,
    }
