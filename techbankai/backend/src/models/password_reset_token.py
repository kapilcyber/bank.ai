"""Password Reset Token SQLAlchemy model."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from datetime import datetime
from src.config.database import Base


class PasswordResetToken(Base):
    """Password reset token database model."""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, email='{self.email}', used={self.used})>"

