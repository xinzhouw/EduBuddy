from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=False)
    grade = Column(String(10), nullable=False)
    role = Column(String(20), nullable=False, default="student")  # student/teacher/parent/admin
    phone = Column(String(20), nullable=True)        # 手机号码
    gender = Column(String(10), nullable=True)        # 性别：male / female / other
    age = Column(Integer, nullable=True)              # 年龄
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_date = Column(Date, nullable=True)    # 最后登录日期（用于每日建议触发）
    last_login = Column(DateTime, nullable=True)     # 最后登录时间（用于管理后台统计）
    login_count = Column(Integer, nullable=False, default=0)  # 登录次数统计
    language = Column(String(10), nullable=False, default='zh')  # 界面语言：zh / en
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 密码重置字段
    password_reset_code = Column(String(6), nullable=True)
    reset_code_expiry = Column(DateTime, nullable=True)
    reset_attempts = Column(Integer, default=0)
    reset_code_locked_until = Column(DateTime, nullable=True)

    # 关系
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
