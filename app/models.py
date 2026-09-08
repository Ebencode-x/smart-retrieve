from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    student = "student"
    security = "security"          # legacy value, kept in DB enum, no longer assigned to new users
    gate_security = "gate_security"
    invigilator = "invigilator"
    exams_officer = "exams_officer"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    registration_number = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda e: [v.value for v in e]), default=UserRole.student, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reports = relationship("IDCardReport", back_populates="reporter")
    passes = relationship("ClearancePass", back_populates="owner", foreign_keys="ClearancePass.owner_id")

class ReportStatus(str, enum.Enum):
    lost = "lost"
    found = "found"
    resolved = "resolved"

class ReportType(str, enum.Enum):
    lost = "lost"              # haijulikani iko wapi kabisa
    forgotten = "forgotten"    # anajua eneo (nyumbani/bwenini), kasahau tu

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String, nullable=False)
    room = Column(String, nullable=False)
    exam_date = Column(Date, nullable=False)
    exam_time = Column(Time, nullable=False)
    reports = relationship("IDCardReport", back_populates="exam")

class IDCardReport(Base):
    __tablename__ = "id_card_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    card_owner_reg_no = Column(String, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.lost, nullable=False)
    report_type = Column(Enum(ReportType), default=ReportType.lost, nullable=False)
    declaration_confirmed = Column(Boolean, default=False, nullable=False)
    tier = Column(Integer, nullable=False)  # 1, 2, or 3 — computed at creation from lead time before exam
    location = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    reporter = relationship("User", back_populates="reports")
    exam = relationship("Exam", back_populates="reports")
    clearance_passes = relationship("ClearancePass", back_populates="report")

class ClearancePass(Base):
    __tablename__ = "clearance_passes"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_id = Column(Integer, ForeignKey("id_card_reports.id"), nullable=False)
    totp_secret = Column(String, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="passes", foreign_keys=[owner_id])
    report = relationship("IDCardReport", back_populates="clearance_passes")
