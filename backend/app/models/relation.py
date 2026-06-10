from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class UserRelation(Base):
    """教师/家长 与 学生 的关联关系"""
    __tablename__ = "user_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(20), nullable=False)  # teacher / parent
    class_name = Column(String(50), nullable=True)      # 班级名称（教师用）
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class BindCode(Base):
    """学生生成供家长/教师绑定的临时码"""
    __tablename__ = "bind_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(10), nullable=False, unique=True, index=True)
    relation_type = Column(String(20), nullable=False)  # teacher / parent
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ClassGroup(Base):
    """教师创建的班级"""
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    invite_code = Column(String(10), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
