from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    subject = Column(String(20), nullable=True)
    file_type = Column(String(10), nullable=False)  # 'pdf'/'docx'/'jpg'/'png'
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # 'pending'/'processing'/'done'/'error'
    content_text = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)  # JSON array
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)


class StudyLog(Base):
    __tablename__ = "study_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    subject = Column(String(20), nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    activity_type = Column(String(20), nullable=False)  # 'ai_chat'/'notes'/'quiz'/'review'/'plan'/'docs'
    created_at = Column(DateTime, nullable=False, server_default=func.now())
