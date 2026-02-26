"""Job Opening SQLAlchemy model."""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from src.config.database import Base


class JobOpening(Base):
    """Job Opening database model for public job postings."""
    __tablename__ = "job_openings"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    business_area = Column(String(100), nullable=False, index=True)
    experience_required = Column(String(20), nullable=True)  # e.g. "0-1", "1+", "2+", ... "50+"
    job_type = Column(String(50), nullable=True)  # internship, full_time, remote, hybrid, contract
    description = Column(Text)
    jd_file_url = Column(String(500), nullable=True)
    status = Column(String(20), default="active", index=True)  # "active" or "inactive"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(100))  # Admin email
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<JobOpening(job_id='{self.job_id}', title='{self.title}')>"

