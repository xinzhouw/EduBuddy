import json
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from jose import jwt
from app.database import get_db
from app.config import get_settings
from app.dependencies import get_current_user, require_rate_limit, get_client_ip, verify_refresh_token
from app.models.user import User
from app.security import hash_password, verify_password
from app.schemas.auth import (
    UserRegister, UserLogin, UserOut, TokenData, UserUpdate, PasswordChange,
    PasswordStrengthResponse, ChangePasswordRequest, PasswordValidateRequest,
    RefreshTokenRequest, RefreshTokenResponse
)
from app.utils.password_validator import validate_password_strength, check_password_validity
from app.utils.rate_limiter import check_rate_limit_for_endpoint

router = APIRouter(prefix="/api/auth", tags=["认证"])
settings = get_settings()


# 错误码常量
class LoginErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVER_ERROR = "SERVER_ERROR"


def create_token(user_id: int, token_type: str = "access") -> str:
    """
    创建 JWT 令牌

    Args:
        user_id: 用户 ID
        token_type: 令牌类型 ("access" 或 "refresh")

    Returns:
        JWT 令牌字符串
    """
    if token_type == "refresh":
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    else:  # access token
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": token_type},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


@router.post("/password/validate")
def validate_password_endpoint(req: PasswordValidateRequest, request: Request):
    """
    实时检查密码强度

    不检查已注册密码或其他业务逻辑，仅返回技术强度评分。
    前端用此 API 提供实时反馈。
    """
    # 检查速率限制
    ip_address = get_client_ip(request)
    allowed, _, retry_after = check_rate_limit_for_endpoint(ip_address, "password_validate")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
            headers={"Retry-After": str(retry_after)},
        )

    if not req.password:
        raise HTTPException(status_code=400, detail="密码参数缺失")
    result = validate_password_strength(req.password)
    return PasswordStrengthResponse(
        score=result.score,
        strength=result.strength.value,
        issues=result.issues,
    )


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db), request: Request = None):
    # 检查速率限制
    if request:
        ip_address = get_client_ip(request)
        allowed, _, retry_after = check_rate_limit_for_endpoint(ip_address, "register")
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
                headers={"Retry-After": str(retry_after)},
            )

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    # 检查密码强度（注册时强制）
    is_valid, error_msg = check_password_validity(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"密码不符合要求: {error_msg}")
    hashed = hash_password(data.password)
    role = data.role if data.role in ("student", "teacher", "parent") else "student"
    user = User(email=data.email, password=hashed, nickname=data.nickname, grade=data.grade, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_token(user.id, "access")
    refresh_token = create_token(user.id, "refresh")

    # 创建 JSON 响应
    user_data = UserOut.model_validate(user)
    response = JSONResponse(
        status_code=200,
        content={
            "access_token": access_token,  # 仍在响应中（向后兼容）
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": json.loads(user_data.model_dump_json()),
        }
    )

    # 设置 httpOnly cookie
    response.set_cookie(
        key=settings.cookie_access_token_name,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
    )

    return response


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db), request: Request = None):
    # 检查速率限制
    if request:
        ip_address = get_client_ip(request)
        allowed, _, retry_after = check_rate_limit_for_endpoint(ip_address, "login")
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": 429,
                    "error_code": LoginErrorCode.RATE_LIMIT_EXCEEDED,
                    "message": f"登录过于频繁，请在 {retry_after} 秒后重试",
                    "data": None,
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        # Always return the same error message regardless of whether email exists or password is wrong
        # This prevents user enumeration attacks
        raise HTTPException(
            status_code=401,
            detail={
                "code": 401,
                "error_code": LoginErrorCode.INVALID_CREDENTIALS,
                "message": "邮箱或密码错误",
                "data": None,
                "retry_after": None,
            },
        )
    # 检查账户是否被禁用
    # 使用 401 而非 403，防止攻击者通过状态码差异枚举已注册邮箱
    # error_code 仍为 ACCOUNT_DISABLED，供前端区分；对外消息保持统一
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={
                "code": 401,
                "error_code": LoginErrorCode.ACCOUNT_DISABLED,
                "message": "邮箱或密码错误",
                "data": None,
                "retry_after": None,
            },
        )
    # 更新最后登录日期（用于每日建议触发逻辑）
    user.last_login_date = date.today()
    # 更新登录统计（用于管理后台）
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    db.commit()
    access_token = create_token(user.id, "access")
    refresh_token = create_token(user.id, "refresh")

    # 创建 JSON 响应
    user_data = UserOut.model_validate(user)
    response = JSONResponse(
        status_code=200,
        content={
            "code": 200,
            "message": "登录成功",
            "data": {
                "access_token": access_token,  # 仍在响应中（向后兼容）
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60,
                "user": json.loads(user_data.model_dump_json()),
            },
        }
    )

    # 设置 httpOnly cookie
    response.set_cookie(
        key=settings.cookie_access_token_name,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
    )

    return response


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


@router.post("/refresh")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    使用刷新令牌获取新的访问令牌

    Args:
        req: 包含刷新令牌的请求

    Returns:
        新的访问令牌和可选的新刷新令牌
    """
    # 验证刷新令牌
    user_id = verify_refresh_token(req.refresh_token)

    # 确保用户存在且活跃
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")

    # 颁发新的访问令牌
    new_access_token = create_token(user_id, "access")

    # 可选：颁发新的刷新令牌（以轮换旧令牌）
    new_refresh_token = create_token(user_id, "refresh")

    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/change-password")
def change_password_post(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(req.old_password, user.password):
        raise HTTPException(status_code=401, detail="旧密码错误")

    # 不能与旧密码相同
    if req.old_password == req.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    # 检查新密码强度
    is_valid, error_msg = check_password_validity(req.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"新密码不符合要求: {error_msg}")

    # 更新密码
    user.password = hash_password(req.new_password)
    db.commit()

    return {"message": "密码已修改"}


@router.delete("/me")
def delete_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除当前用户账号及其所有关联数据（不可恢复）。

    SQLite 默认不强制外键约束（PRAGMA foreign_keys=OFF），因此这里
    显式按表清除该用户的所有关联数据，确保彻底删除、不留孤儿记录。
    """
    from app.models.note import Note, Flashcard, ChatSession, ChatMessage
    from app.models.quiz import QuizSession, Question, QuizAnswer
    from app.models.wrong_item import WrongItem, WrongReview
    from app.models.study_plan import StudyPlan, PlanTask, Pomodoro
    from app.models.document import Document, StudyLog
    from app.models.homework import HomeworkGrading
    from app.models.advice import DailyAdvice, AdviceAction
    from app.models.relation import UserRelation, BindCode, ClassGroup

    uid = current_user.id

    # 1. 收集父记录 id（部分子表只关联父表 id，没有 user_id 字段）
    quiz_session_ids = [s.id for s in db.query(QuizSession.id).filter(QuizSession.user_id == uid)]

    # 2. Question 表只有 session_id（无 user_id），需用 quiz_session_id 删除
    if quiz_session_ids:
        db.query(Question).filter(Question.session_id.in_(quiz_session_ids)).delete(synchronize_session=False)

    # 3. 删除所有带 user_id 的表（顺序：先子表后父表，避免外键约束启用时报错）
    for model in (
        QuizAnswer, WrongReview, ChatMessage, AdviceAction,
        PlanTask, Pomodoro, StudyLog,
        QuizSession, ChatSession, WrongItem, Flashcard, Note,
        StudyPlan, Document, HomeworkGrading, DailyAdvice,
    ):
        db.query(model).filter(model.user_id == uid).delete(synchronize_session=False)

    # 4. 关联关系表（字段命名不统一：BindCode.student_id / ClassGroup.teacher_id /
    #    UserRelation.observer_id|student_id）
    db.query(BindCode).filter(BindCode.student_id == uid).delete(synchronize_session=False)
    db.query(UserRelation).filter(
        (UserRelation.observer_id == uid) | (UserRelation.student_id == uid)
    ).delete(synchronize_session=False)
    db.query(ClassGroup).filter(ClassGroup.teacher_id == uid).delete(synchronize_session=False)


    # 5. 删除用户本身
    db.query(User).filter(User.id == uid).delete(synchronize_session=False)
    db.commit()
    return {"code": 200, "message": "账号已成功删除"}


