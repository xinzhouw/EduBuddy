from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class DailyAdvice(Base):
    """每日学习建议记录"""
    __tablename__ = "daily_advices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    advices_json = Column(Text, nullable=False)    # JSON 数组，存储当日所有建议条目
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    shown_at = Column(DateTime, nullable=True)     # 用户首次看到时间


class AdviceAction(Base):
    """用户对建议的响应记录（用于追踪建议执行情况）"""
    __tablename__ = "advice_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    advice_id = Column(Integer, ForeignKey("daily_advices.id", ondelete="CASCADE"), nullable=False, index=True)
    advice_item_id = Column(String(50), nullable=False)  # 建议条目的唯一 ID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    acted_at = Column(DateTime, nullable=False, server_default=func.now())
    outcome = Column(String(50), nullable=True)  # 执行后的效果评估（后台计算填充）
