from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class ChatImage(Base):
    __tablename__ = "chat_images"

    id = Column(String(100), primary_key=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)
    ocr_text = Column(Text, nullable=True)
    vision_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # 索引
    __table_args__ = (
        Index("idx_chat_image_session_user", "session_id", "user_id"),
        Index("idx_chat_image_created", "created_at"),
    )

    # 关系
    session = relationship("ChatSession", back_populates="images")
    user = relationship("User")
