from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class ResumeUpload(Base):
    __tablename__ = "resume_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    content_type = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # ✅ Relationship: one resume upload → one parsed text
    parsed_text = relationship("ResumeText", back_populates="resume", uselist=False)


class ResumeText(Base):
    __tablename__ = "resume_texts"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resume_uploads.id"), nullable=False)
    content = Column(Text, nullable=False)

    # ✅ Back reference to ResumeUpload
    resume = relationship("ResumeUpload", back_populates="parsed_text")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(100))
    doj = Column(Date)
    location = Column(String(100))
    department = Column(String(100))
