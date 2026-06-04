from datetime import date, datetime
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.document import StudyLog
from app.models.wrong_item import WrongItem
from app.schemas.document import StudyLogCreate
from app.services import stats_service

router = APIRouter(prefix="/api/stats", tags=["学习统计"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today_minutes = stats_service.get_today_study_minutes(db, current_user.id)
    streak = stats_service.get_streak_days(db, current_user.id)
    total_days = stats_service.get_total_study_days(db, current_user.id)
    total_questions = stats_service.get_total_questions_done(db, current_user.id)
    avg_accuracy = stats_service.get_average_accuracy(db, current_user.id)
    wrong_count = db.query(WrongItem).filter(WrongItem.user_id == current_user.id).count()
    mastered_count = db.query(WrongItem).filter(
        WrongItem.user_id == current_user.id, WrongItem.mastery == "mastered"
    ).count()

    return {"code": 200, "data": {
        "today_study_minutes": today_minutes,
        "streak_days": streak,
        "total_study_days": total_days,
        "total_questions_done": total_questions,
        "average_accuracy": avg_accuracy,
        "wrong_book_count": wrong_count,
        "mastered_count": mastered_count,
        # 服务器时间，供前端按服务器时区显示问候语 / 日期。
        # 直接返回拆解好的字段，避免前端再次解析字符串时受浏览器时区影响。
        "server_time": _build_server_time(),
    }}


def _build_server_time() -> dict:
    """返回服务器本地时间的各个分量，供前端直接使用，避免时区歧义。"""
    now = datetime.now().astimezone()
    return {
        # 带时区偏移的 ISO 8601 字符串（例如 2026-06-04T16:13:00+08:00）
        "iso": now.isoformat(),
        "hour": now.hour,          # 0-23
        "month": now.month,        # 1-12
        "day": now.day,            # 1-31
        "weekday": now.isoweekday() % 7,  # 0=周日, 1=周一 ... 6=周六（与 JS getDay 对齐）
    }



@router.get("/study-time")
def get_study_time(
    period: str = "week",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = stats_service.get_study_time_trend(db, current_user.id, period)
    return {"code": 200, "data": data}


@router.get("/accuracy-by-subject")
def get_accuracy_by_subject(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = stats_service.get_accuracy_by_subject(db, current_user.id)
    return {"code": 200, "data": data}


@router.get("/wrong-book-distribution")
def get_wrong_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = stats_service.get_wrong_book_distribution(db, current_user.id)
    return {"code": 200, "data": data}


@router.post("/study-log")
def record_study_log(
    data: StudyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = StudyLog(
        user_id=current_user.id,
        date=date.today(),
        subject=data.subject,
        duration_minutes=data.duration_minutes,
        activity_type=data.activity_type,
    )
    db.add(log)
    db.commit()
    return {"code": 200, "message": "学习时长已记录"}
