from datetime import datetime, timedelta
import pyotp
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ClearancePass, User
from app.schemas import PassOut, PassVerify
from app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/passes", tags=["passes"])

PASS_VALIDITY_MINUTES = 10


@router.post("/generate", response_model=PassOut, status_code=201)
def generate_pass(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, interval=PASS_VALIDITY_MINUTES * 60)

    clearance_pass = ClearancePass(
        owner_id=current_user.id,
        totp_secret=secret,
        expires_at=datetime.utcnow() + timedelta(minutes=PASS_VALIDITY_MINUTES),
    )
    db.add(clearance_pass)
    db.commit()
    db.refresh(clearance_pass)

    return PassOut(
        id=clearance_pass.id,
        expires_at=clearance_pass.expires_at,
        is_used=clearance_pass.is_used,
        code=totp.now(),
    )


@router.post("/verify")
def verify_pass(
    payload: PassVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("security")),
):
    clearance_pass = db.query(ClearancePass).filter(ClearancePass.id == payload.pass_id).first()
    if not clearance_pass:
        raise HTTPException(status_code=404, detail="Pass haijapatikana")
    if clearance_pass.is_used:
        raise HTTPException(status_code=400, detail="Pass hii tayari imetumika")
    if clearance_pass.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Pass imeisha muda")

    totp = pyotp.TOTP(clearance_pass.totp_secret, interval=PASS_VALIDITY_MINUTES * 60)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Code si sahihi")

    clearance_pass.is_used = True
    clearance_pass.verified_by_id = current_user.id
    db.commit()

    return {"status": "imethibitishwa", "owner_id": clearance_pass.owner_id}
