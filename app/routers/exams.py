from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Exam, User
from app.schemas import ExamCreate, ExamOut
from app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/exams", tags=["exams"])

@router.post("/", response_model=ExamOut, status_code=201)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("security")),
):
    exam = Exam(
        course_code=payload.course_code,
        room=payload.room,
        exam_date=payload.exam_date,
        exam_time=payload.exam_time,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam

@router.get("/", response_model=list[ExamOut])
def list_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Exam).order_by(Exam.exam_date, Exam.exam_time).all()
