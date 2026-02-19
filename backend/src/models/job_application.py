"""Job Application SQLAlchemy model for career page applicants."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from src.config.database import Base


class JobApplication(Base):
    """Tracks applicants who applied via the career page for a specific job."""
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey("job_openings.job_id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    applicant_name = Column(String(255), nullable=True)
    applicant_email = Column(String(255), nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("job_id", "resume_id", name="uq_job_application_job_resume"),
    )

    def __repr__(self):
        return f"<JobApplication(job_id='{self.job_id}', resume_id={self.resume_id})>"
