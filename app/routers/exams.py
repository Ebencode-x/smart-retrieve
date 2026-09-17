from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from io import BytesIO
from app.database import get_db
from app.models import Exam, User
from app.schemas import ExamCreate, ExamUpdate, ExamOut
from app.dependencies import get_current_user, require_role

router = APIRouter(prefix="/exams", tags=["exams"])

@router.post("/", response_model=ExamOut, status_code=201)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("exams_officer", "admin")),
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

@router.put("/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("exams_officer", "admin")),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    db.commit()
    db.refresh(exam)
    return exam

@router.delete("/{exam_id}", status_code=204)
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("exams_officer", "admin")),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    try:
        db.delete(exam)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete this exam — there are ID reports linked to it",
        )

@router.get("/export/xlsx")
def export_exams_xlsx(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from openpyxl import Workbook

    exams = db.query(Exam).order_by(Exam.exam_date, Exam.exam_time).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Exam Schedule"
    ws.append(["ID", "Course Code", "Room", "Date", "Time"])
    for e in exams:
        ws.append([e.id, e.course_code, e.room, str(e.exam_date), str(e.exam_time)])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=exam_schedule.xlsx"},
    )
