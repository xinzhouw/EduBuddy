from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    grade: str
    role: Optional[str] = "student"  # student/teacher/parent


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    grade: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    email: str
    nickname: str
    grade: str
    role: str = "student"
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[object] = None


class PasswordValidateRequest(BaseModel):
    password: str


class PasswordStrengthResponse(BaseModel):
    score: int  # 0-100
    strength: str  # "weak" | "medium" | "strong"
    issues: list[str]


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
