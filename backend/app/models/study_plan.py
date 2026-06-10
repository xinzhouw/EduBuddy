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
    study_style = Column(String(20), nullable=True, default="balanced")  # balanced/intensive/steady
    preferred_times = Column(Text, nullable=True, default="[]")  # JSON array: morning/afternoon/evening
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
    # 学习内容功能
    ai_content = Column(Text, nullable=True)           # AI 生成的学习内容（Markdown）
    submission_text = Column(Text, nullable=True)      # 用户提交的文字学习成果
    submission_image = Column(String(500), nullable=True)  # 用户上传的图片路径
    evaluation = Column(Text, nullable=True)           # AI 评判结果（Markdown）
    eval_score = Column(Float, nullable=True)          # AI 评判分数（0-100）
    completion_mode = Column(String(20), nullable=True)  # 'manual'/'ai_content'/'submission'
    # 练习题功能
    quiz_data = Column(Text, nullable=True)              # AI 生成的练习题（JSON）
    quiz_submission = Column(Text, nullable=True)        # 学生提交的答案（JSON）
    quiz_evaluation = Column(Text, nullable=True)        # AI 评判结果（Markdown）
    quiz_score = Column(Float, nullable=True)            # 练习题得分（0-100）


class Pomodoro(Base):
    __tablename__ = "pomodoros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(20), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=25)
    completed = Column(Boolean, nullable=False, default=True)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
