from pydantic import BaseModel, EmailStr, Field
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
    language: str = 'zh'
    created_at: datetime

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
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


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="用户邮箱")


class ForgotPasswordResponse(BaseModel):
    code: int
    message: str
    data: dict = None


class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="用户邮箱")
    code: str = Field(..., description="6位验证码")
    new_password: str = Field(..., description="新密码")


class ResetPasswordResponse(BaseModel):
    code: int
    message: str
