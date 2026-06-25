from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    feature = Column(String(50), nullable=False, index=True)  # ai_chat, notes, wrong_book, quiz, study_plan, homework, monitor, auth, admin, others
    action = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    endpoint = Column(String(255), nullable=False)
    ip_address = Column(String(45))  # IPv4 或 IPv6
    city = Column(String(100))
    country = Column(String(100))
    status_code = Column(Integer)

    # 关系
    user = relationship("User", back_populates="audit_logs")
