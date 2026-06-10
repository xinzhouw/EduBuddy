import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.relation import UserRelation, BindCode, ClassGroup

router = APIRouter(prefix="/api/relations", tags=["用户关系"])


def _gen_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _gen_invite_code(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class BindCodeRequest(BaseModel):
    relation_type: str  # teacher / parent


class BindRequest(BaseModel):
    code: str
    relation_type: str  # teacher / parent


class ClassCreateRequest(BaseModel):
    name: str


class ClassJoinRequest(BaseModel):
    invite_code: str


@router.post("/bind-code")
def create_bind_code(
    data: BindCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生生成绑定码，供家长/教师使用（有效期24小时）"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="只有学生才能生成绑定码")

    # 生成唯一码
    for _ in range(10):
        code = _gen_code(6)
        exists = db.query(BindCode).filter(BindCode.code == code, BindCode.used == False).first()
        if not exists:
            break

    bind = BindCode(
        student_id=current_user.id,
        code=code,
        relation_type=data.relation_type,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(bind)
    db.commit()
    return {"code": 200, "data": {"code": code, "expires_in_hours": 24}}


@router.post("/bind")
def bind_student(
    data: BindRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教师/家长使用绑定码绑定学生"""
    if current_user.role not in ("teacher", "parent"):
        raise HTTPException(status_code=403, detail="只有教师或家长才能使用绑定码")

    bind = db.query(BindCode).filter(
        BindCode.code == data.code,
        BindCode.used == False,
        BindCode.relation_type == data.relation_type,
    ).first()
    if not bind:
        raise HTTPException(status_code=404, detail="绑定码无效或已使用")
    if bind.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="绑定码已过期")

    # 检查是否已绑定
    existing = db.query(UserRelation).filter(
        UserRelation.observer_id == current_user.id,
        UserRelation.student_id == bind.student_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已绑定该学生")

    relation = UserRelation(
        observer_id=current_user.id,
        student_id=bind.student_id,
        relation_type=data.relation_type,
    )
    db.add(relation)
    bind.used = True
    db.commit()
    return {"code": 200, "message": "绑定成功"}


@router.get("/students")
def get_my_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取关联学生列表（教师/家长）"""
    if current_user.role not in ("teacher", "parent"):
        raise HTTPException(status_code=403, detail="权限不足")

    relations = db.query(UserRelation).filter(
        UserRelation.observer_id == current_user.id
    ).all()

    result = []
    for rel in relations:
        student = db.query(User).filter(User.id == rel.student_id).first()
        if student:
            result.append({
                "relation_id": rel.id,
                "student_id": student.id,
                "nickname": student.nickname,
                "grade": student.grade,
                "relation_type": rel.relation_type,
                "class_name": rel.class_name,
            })
    return {"code": 200, "data": result}


@router.get("/observers")
def get_my_observers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取关联的教师/家长列表（学生端）"""
    relations = db.query(UserRelation).filter(
        UserRelation.student_id == current_user.id
    ).all()

    result = []
    for rel in relations:
        observer = db.query(User).filter(User.id == rel.observer_id).first()
        if observer:
            result.append({
                "relation_id": rel.id,
                "observer_id": observer.id,
                "nickname": observer.nickname,
                "role": observer.role,
                "relation_type": rel.relation_type,
            })
    return {"code": 200, "data": result}


@router.delete("/{relation_id}")
def remove_relation(
    relation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """解除关联"""
    relation = db.query(UserRelation).filter(UserRelation.id == relation_id).first()
    if not relation:
        raise HTTPException(status_code=404, detail="关联不存在")
    if relation.observer_id != current_user.id and relation.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")
    db.delete(relation)
    db.commit()
    return {"code": 200, "message": "已解除关联"}


@router.post("/classes")
def create_class(
    data: ClassCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教师创建班级"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="只有教师才能创建班级")

    for _ in range(10):
        invite_code = _gen_invite_code(8)
        exists = db.query(ClassGroup).filter(ClassGroup.invite_code == invite_code).first()
        if not exists:
            break

    cls = ClassGroup(
        teacher_id=current_user.id,
        name=data.name,
        invite_code=invite_code,
    )
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return {"code": 200, "data": {"id": cls.id, "name": cls.name, "invite_code": cls.invite_code}}


@router.get("/classes")
def get_my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我创建的班级列表（教师）"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="权限不足")

    classes = db.query(ClassGroup).filter(ClassGroup.teacher_id == current_user.id).all()
    return {
        "code": 200,
        "data": [{"id": c.id, "name": c.name, "invite_code": c.invite_code} for c in classes],
    }


@router.post("/classes/join")
def join_class(
    data: ClassJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生通过邀请码加入班级"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="只有学生才能加入班级")

    cls = db.query(ClassGroup).filter(ClassGroup.invite_code == data.invite_code).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级邀请码无效")

    existing = db.query(UserRelation).filter(
        UserRelation.observer_id == cls.teacher_id,
        UserRelation.student_id == current_user.id,
    ).first()
    if existing:
        return {"code": 200, "message": "已在该班级中"}

    relation = UserRelation(
        observer_id=cls.teacher_id,
        student_id=current_user.id,
        relation_type="teacher",
        class_name=cls.name,
    )
    db.add(relation)
    db.commit()
    return {"code": 200, "message": f"成功加入班级：{cls.name}"}
