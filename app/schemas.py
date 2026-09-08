from pydantic import BaseModel, EmailStr
from datetime import datetime, date, time
from app.models import UserRole, ReportStatus, ReportType

class UserCreate(BaseModel):
    full_name: str
    registration_number: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.student
    security_access_code: str | None = None

class UserOut(BaseModel):
    id: int
    full_name: str
    registration_number: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None

class RoleUpdate(BaseModel):
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ExamCreate(BaseModel):
    course_code: str
    room: str
    exam_date: date
    exam_time: time

class ExamUpdate(BaseModel):
    course_code: str | None = None
    room: str | None = None
    exam_date: date | None = None
    exam_time: time | None = None

class ExamOut(BaseModel):
    id: int
    course_code: str
    room: str
    exam_date: date
    exam_time: time
    class Config:
        from_attributes = True

class ReportCreate(BaseModel):
    card_owner_reg_no: str
    exam_id: int
    status: ReportStatus = ReportStatus.lost
    report_type: ReportType
    declaration_confirmed: bool
    location: str | None = None
    description: str | None = None

class ReportOut(BaseModel):
    id: int
    reporter_id: int
    exam_id: int
    card_owner_reg_no: str
    status: ReportStatus
    report_type: ReportType
    declaration_confirmed: bool
    tier: int
    location: str | None
    description: str | None
    created_at: datetime
    resolved_at: datetime | None
    class Config:
        from_attributes = True

class PassGenerate(BaseModel):
    report_id: int


class PassOut(BaseModel):
    id: int
    report_id: int
    expires_at: datetime
    is_used: bool
    code: str  # inaonyeshwa mara moja tu, wakati wa kuundwa
    class Config:
        from_attributes = True

class PassVerify(BaseModel):
    pass_id: int
    code: str
