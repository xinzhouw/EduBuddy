from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt
from app.database import get_db
from app.config import get_settings
from app.dependencies import get_current_user
from app.models.user import User
from app.security import hash_password, verify_password
from app.schemas.auth import UserRegister, UserLogin, UserOut, TokenData, UserUpdate, PasswordChange

router = APIRouter(prefix="/api/auth", tags=["认证"])
settings = get_settings()


def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.access_token_expire_days)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    hashed = hash_password(data.password)
    user = User(email=data.email, password=hashed, nickname=data.nickname, grade=data.grade)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"code": 200, "message": "注册成功", "data": UserOut.model_validate(user)}


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = create_token(user.id)
    return {
        "code": 200,
        "message": "登录成功",
        "data": TokenData(
            access_token=token,
            token_type="bearer",
            expires_in=settings.access_token_expire_days * 86400,
            user=UserOut.model_validate(user),
        ),
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"code": 200, "data": UserOut.model_validate(current_user)}


@router.put("/me")
def update_me(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.grade is not None:
        current_user.grade = data.grade
    if data.phone is not None:
        current_user.phone = data.phone
    if data.gender is not None:
        current_user.gender = data.gender
    if data.age is not None:
        current_user.age = data.age
    db.commit()
    db.refresh(current_user)
    return {"code": 200, "message": "更新成功", "data": UserOut.model_validate(current_user)}


@router.put("/password")
def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    current_user.password = hash_password(data.new_password)
    db.commit()
    return {"code": 200, "message": "密码修改成功"}
