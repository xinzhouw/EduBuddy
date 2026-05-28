from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class WrongItem(Base):
    __tablename__ = "wrong_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    user_wrong_answer = Column(Text, nullable=True)
    subject = Column(String(20), nullable=False, index=True)
    tags = Column(Text, nullable=False, default="[]")  # JSON array
    source = Column(String(20), nullable=False, default="manual")  # 'quiz'/'manual'/'ai_chat'
    source_id = Column(String(100), nullable=True)
    mastery = Column(String(20), nullable=False, default="unmastered", index=True)
    review_count = Column(Integer, nullable=False, default=0)
    next_review_at = Column(Date, nullable=True, index=True)
    ai_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class WrongReview(Base):
    __tablename__ = "wrong_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wrong_item_id = Column(Integer, ForeignKey("wrong_items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    reviewed_at = Column(DateTime, nullable=False, server_default=func.now())
