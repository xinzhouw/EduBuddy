from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subjects = Column(Text, nullable=False)  # JSON array
    exam_date = Column(Date, nullable=False)
    daily_hours = Column(Float, nullable=False)
    weak_subjects = Column(Text, nullable=False, default="[]")  # JSON array
    start_date = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    subject = Column(String(20), nullable=False)
    topic = Column(String(100), nullable=False)
    task_type = Column(String(20), nullable=False)  # 'study'/'practice'/'review'
    duration_minutes = Column(Integer, nullable=False)
    is_done = Column(Boolean, nullable=False, default=False)
    done_at = Column(DateTime, nullable=True)
    order_num = Column(Integer, nullable=False, default=1)


class Pomodoro(Base):
    __tablename__ = "pomodoros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(20), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=25)
    completed = Column(Boolean, nullable=False, default=True)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
