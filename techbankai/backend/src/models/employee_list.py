"""Models for company employee list and app config."""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from src.config.database import Base


class AppConfig(Base):
    """Key-value config (e.g. employee_verification_enabled, employee_list_source)."""
    __tablename__ = "app_config"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)


class CompanyEmployeeList(Base):
    """Uploaded employee list for verification (employee_id, email, full_name)."""
    __tablename__ = "company_employee_list"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
