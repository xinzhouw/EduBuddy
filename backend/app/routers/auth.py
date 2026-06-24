from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt
from app.database import get_db
from app.config import get_settings
from app.dependencies import get_current_user
from app.models.user import User
from app.security import hash_password, verify_password
from app.schemas.auth import UserRegister, UserLogin, UserOut, TokenData, UserUpdate, PasswordChange, PasswordStrengthResponse, ChangePasswordRequest, PasswordValidateRequest
from app.utils.password_validator import validate_password_strength, check_password_validity

router = APIRouter(prefix="/api/auth", tags=["认证"])
settings = get_settings()


def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.access_token_expire_days)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


@router.post("/password/validate")
def validate_password_endpoint(req: PasswordValidateRequest):
    """
    实时检查密码强度

    不检查已注册密码或其他业务逻辑，仅返回技术强度评分。
    前端用此 API 提供实时反馈。
    """
    if not req.password:
        raise HTTPException(status_code=400, detail="密码参数缺失")
    result = validate_password_strength(req.password)
    return PasswordStrengthResponse(
        score=result.score,
        strength=result.strength.value,
        issues=result.issues,
    )


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
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
    token = create_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user),
    }


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    # 更新最后登录日期（用于每日建议触发逻辑）
    user.last_login_date = date.today()
    db.commit()
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


