from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    subject = Column(String(20), nullable=False, index=True)
    content = Column(Text, nullable=False, default="")
    ai_summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    subject = Column(String(20), nullable=False)
    tags = Column(Text, nullable=False, default="[]")  # JSON array
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    subject = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    feedback = Column(String(20), nullable=True)  # 'thumbs_up' / 'thumbs_down'
    feedback_reason = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        # 复合索引：(session_id, created_at) 用于按时间排序查询
        # (user_id) 用于用户维度的查询
        {
            'indexes': [
                ('session_id', 'created_at'),
            ]
        },
    )
