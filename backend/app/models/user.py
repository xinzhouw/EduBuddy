from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=False)
    grade = Column(String(10), nullable=False)
    phone = Column(String(20), nullable=True)        # 手机号码
    gender = Column(String(10), nullable=True)        # 性别：male / female / other
    age = Column(Integer, nullable=True)              # 年龄
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
