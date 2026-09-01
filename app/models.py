from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    student = "student"
    security = "security"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    registration_number = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("IDCardReport", back_populates="reporter")
    passes = relationship("ClearancePass", back_populates="owner", foreign_keys="ClearancePass.owner_id")


class ReportStatus(str, enum.Enum):
    lost = "lost"
    found = "found"
    resolved = "resolved"

class IDCardReport(Base):
    __tablename__ = "id_card_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_owner_reg_no = Column(String, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.lost, nullable=False)
    location = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    reporter = relationship("User", back_populates="reports")


class ClearancePass(Base):
    __tablename__ = "clearance_passes"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    totp_secret = Column(String, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="passes", foreign_keys=[owner_id])
