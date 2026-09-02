import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, UserOut, UserLogin, Token
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role == UserRole.security:
        expected_code = os.getenv("SECURITY_ACCESS_CODE")
        if not expected_code or payload.security_access_code != expected_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid security access code. Contact your system administrator.",
            )

    existing = db.query(User).filter(
        (User.email == payload.email) | (User.registration_number == payload.registration_number)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or registration number already registered")
    user = User(
        full_name=payload.full_name,
        registration_number=payload.registration_number,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token)
