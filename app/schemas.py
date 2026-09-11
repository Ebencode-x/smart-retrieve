import re
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from datetime import datetime, date, time
from app.models import UserRole, ReportStatus, ReportType

# Students use MUST's official numeric format, e.g. 25101133370022 —
# starts with the 2-digit intake year (24 or 25) followed by 12 digits.
# Staff/admin roles are not MUST-registry-issued, so they stay free-text.
STUDENT_REGNO_PATTERN = re.compile(r"^(24|25)\d{12}$")


def validate_student_regno(value: str) -> str:
    if not STUDENT_REGNO_PATTERN.match(value):
        raise ValueError(
            "Student registration number must be 14 digits starting with 24 or 25 "
            "(e.g. 25101133370022)"
        )
    return value


class UserCreate(BaseModel):
    full_name: str
    registration_number: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.student
    security_access_code: str | None = None

    @model_validator(mode="after")
    def check_student_regno(self):
        if self.role == UserRole.student:
            validate_student_regno(self.registration_number)
        return self

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

class AdminUserUpdate(BaseModel):
    """Full profile edit for admins — separate from the role-only patch."""
    full_name: str | None = None
    email: EmailStr | None = None
    registration_number: str | None = None

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

class ReportUpdate(BaseModel):
    """Lets the reporter fix a mistake (e.g. wrong reg no) before it's resolved."""
    card_owner_reg_no: str | None = None
    report_type: ReportType | None = None
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
