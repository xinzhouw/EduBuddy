import json
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.document import StudyLog
from app.models.wrong_item import WrongItem
from app.models.study_plan import Pomodoro
from app.models.quiz import QuizAnswer
from app.schemas.document import StudyLogCreate
from app.services import stats_service
from app.services.ai_service import ai_service

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
    plan_stats = stats_service.get_plan_completion_stats(db, current_user.id)

    return {"code": 200, "data": {
        "today_study_minutes": today_minutes,
        "streak_days": streak,
        "total_study_days": total_days,
        "total_questions_done": total_questions,
        "average_accuracy": avg_accuracy,
        "wrong_book_count": wrong_count,
        "mastered_count": mastered_count,
        "plan_today_completion": plan_stats["today_completion"],
        "plan_overall_completion": plan_stats["overall_completion"],
        "plan_today_done": plan_stats["today_done"],
        "plan_today_total": plan_stats["today_total"],
        "server_time": _build_server_time(),
    }}


def _build_server_time() -> dict:
    """返回服务器本地时间的各个分量，供前端直接使用，避免时区歧义。"""
    now = datetime.now().astimezone()
    return {
        "iso": now.isoformat(),
        "hour": now.hour,
        "month": now.month,
        "day": now.day,
        "weekday": now.isoweekday() % 7,
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


@router.get("/radar")
def get_radar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """各学科掌握深度雷达图数据"""
    data = stats_service.get_radar_data(db, current_user.id)
    return {"code": 200, "data": data}


@router.get("/heatmap")
def get_heatmap(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """近3个月学习活跃度热力图数据"""
    data = stats_service.get_heatmap_data(db, current_user.id)
    return {"code": 200, "data": data}


@router.get("/subject-time-distribution")
def get_subject_time_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """近30天各学科学习时长占比"""
    data = stats_service.get_subject_time_distribution(db, current_user.id)
    return {"code": 200, "data": data}


@router.get("/plan-completion")
def get_plan_completion(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """计划完成率统计"""
    data = stats_service.get_plan_completion_stats(db, current_user.id)
    return {"code": 200, "data": data}


@router.post("/generate-report")
async def generate_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发 AI 学习分析报告生成（流式 SSE）"""
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    total_minutes = db.query(func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= thirty_days_ago,
    ).scalar() or 0

    total_days = db.query(func.count(func.distinct(StudyLog.date))).filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= thirty_days_ago,
    ).scalar() or 0

    total_questions = stats_service.get_total_questions_done(db, current_user.id)
    avg_accuracy = stats_service.get_average_accuracy(db, current_user.id)
    accuracy_by_subject = stats_service.get_accuracy_by_subject(db, current_user.id)
    subject_time = stats_service.get_subject_time_distribution(db, current_user.id)

    wrong_count = db.query(WrongItem).filter(WrongItem.user_id == current_user.id).count()
    mastered_count = db.query(WrongItem).filter(
        WrongItem.user_id == current_user.id, WrongItem.mastery == "mastered"
    ).count()

    streak = stats_service.get_streak_days(db, current_user.id)
    pomodoro_count = db.query(Pomodoro).filter(
        Pomodoro.user_id == current_user.id, Pomodoro.completed == True
    ).count()

    stats_30d = {
        "total_study_days": total_days,
        "total_study_minutes": total_minutes,
        "total_questions": total_questions,
        "average_accuracy": avg_accuracy,
        "accuracy_by_subject": accuracy_by_subject,
        "time_by_subject": subject_time,
        "wrong_book_count": wrong_count,
        "mastered_count": mastered_count,
        "streak_days": streak,
        "pomodoro_count": pomodoro_count,
    }

    student_info = {"nickname": current_user.nickname, "grade": current_user.grade}

    async def event_stream():
        async for chunk in ai_service.generate_study_report(student_info, stats_30d):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
