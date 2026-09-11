from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from io import BytesIO
from app.database import get_db
from app.models import User
from app.schemas import UserOut, RoleUpdate, AdminUserUpdate
from app.dependencies import require_role
from app.models import UserRole
from app.schemas import validate_student_regno

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user_profile(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Full profile edit for admins — name/email/reg-no, not just role.
    Students still must keep the 14-digit MUST format; staff stay free-text."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if "registration_number" in data and user.role == UserRole.student:
        try:
            validate_student_regno(data["registration_number"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if "email" in data:
        clash = db.query(User).filter(User.email == data["email"], User.id != user_id).first()
        if clash:
            raise HTTPException(status_code=400, detail="Email already in use by another user")
    if "registration_number" in data:
        clash = db.query(User).filter(
            User.registration_number == data["registration_number"], User.id != user_id
        ).first()
        if clash:
            raise HTTPException(status_code=400, detail="Registration number already in use by another user")

    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete this user — they have reports or passes linked to their account",
        )


@router.get("/export/xlsx")
def export_users_xlsx(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    from openpyxl import Workbook

    users = db.query(User).order_by(User.created_at.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Users"
    ws.append(["ID", "Full Name", "Registration Number", "Email", "Role", "Created At"])
    for u in users:
        ws.append([u.id, u.full_name, u.registration_number, u.email, u.role.value, str(u.created_at)])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=users.xlsx"},
    )
