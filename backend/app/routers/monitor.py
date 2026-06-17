from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.relation import UserRelation
from app.models.document import StudyLog
from app.models.wrong_item import WrongItem
from app.models.study_plan import StudyPlan, PlanTask, Pomodoro
from app.models.quiz import QuizAnswer, Question
from app.services.ai_service import ai_service
from app.services import stats_service

router = APIRouter(prefix="/api/monitor", tags=["监督视图"])


def _check_observer(db: Session, observer: User, student_id: int) -> User:
    """检查观察者是否有权查看该学生数据"""
    if observer.role not in ("teacher", "parent"):
        raise HTTPException(status_code=403, detail="权限不足：需要教师或家长角色")
    relation = db.query(UserRelation).filter(
        UserRelation.observer_id == observer.id,
        UserRelation.student_id == student_id,
    ).first()
    if not relation:
        raise HTTPException(status_code=403, detail="无权查看该学生数据")
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.get("/students")
def get_students_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取关联学生列表及摘要数据（教师/家长）"""
    if current_user.role not in ("teacher", "parent"):
        raise HTTPException(status_code=403, detail="权限不足")

    relations = db.query(UserRelation).filter(
        UserRelation.observer_id == current_user.id
    ).all()

    result = []
    today = date.today()
    for rel in relations:
        student = db.query(User).filter(User.id == rel.student_id).first()
        if not student:
            continue

        # 今日学习时长
        today_minutes = db.query(func.sum(StudyLog.duration_minutes)).filter(
            StudyLog.user_id == student.id,
            StudyLog.date == today,
        ).scalar() or 0

        # 连续打卡 - 使用服务方法，避免重复代码
        streak = stats_service.get_streak_days(db, student.id)

        # 近7天计划完成率
        plan = db.query(StudyPlan).filter(
            StudyPlan.user_id == student.id, StudyPlan.is_active == True
        ).first()
        completion_rate = 0.0
        if plan:
            seven_days_ago = today - timedelta(days=7)
            total_tasks = db.query(PlanTask).filter(
                PlanTask.plan_id == plan.id,
                PlanTask.date >= seven_days_ago,
                PlanTask.date <= today,
            ).count()
            done_tasks = db.query(PlanTask).filter(
                PlanTask.plan_id == plan.id,
                PlanTask.date >= seven_days_ago,
                PlanTask.date <= today,
                PlanTask.is_done == True,
            ).count()
            if total_tasks > 0:
                completion_rate = round(done_tasks / total_tasks, 2)

        result.append({
            "relation_id": rel.id,
            "student_id": student.id,
            "nickname": student.nickname,
            "grade": student.grade,
            "relation_type": rel.relation_type,
            "class_name": rel.class_name,
            "today_study_minutes": today_minutes,
            "streak_days": streak,
            "completion_rate_7d": completion_rate,
            "last_login_date": str(student.last_login_date) if student.last_login_date else None,
        })

    return {"code": 200, "data": result}


@router.get("/students/{student_id}/overview")
def get_student_overview(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生学习概览（教师/家长只读）"""
    student = _check_observer(db, current_user, student_id)

    today_minutes = stats_service.get_today_study_minutes(db, student.id)
    streak = stats_service.get_streak_days(db, student.id)
    total_days = stats_service.get_total_study_days(db, student.id)
    total_questions = stats_service.get_total_questions_done(db, student.id)
    avg_accuracy = stats_service.get_average_accuracy(db, student.id)
    wrong_count = db.query(WrongItem).filter(WrongItem.user_id == student.id).count()
    mastered_count = db.query(WrongItem).filter(
        WrongItem.user_id == student.id, WrongItem.mastery == "mastered"
    ).count()

    return {
        "code": 200,
        "data": {
            "student": {
                "id": student.id,
                "nickname": student.nickname,
                "grade": student.grade,
                "last_login_date": str(student.last_login_date) if student.last_login_date else None,
            },
            "today_study_minutes": today_minutes,
            "streak_days": streak,
            "total_study_days": total_days,
            "total_questions_done": total_questions,
            "average_accuracy": avg_accuracy,
            "wrong_book_count": wrong_count,
            "mastered_count": mastered_count,
        },
    }


@router.get("/students/{student_id}/stats")
def get_student_stats(
    student_id: int,
    period: str = "week",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生详细统计（学习时长趋势、正确率、错题分布）"""
    student = _check_observer(db, current_user, student_id)

    time_trend = stats_service.get_study_time_trend(db, student.id, period)
    accuracy_by_subject = stats_service.get_accuracy_by_subject(db, student.id)
    wrong_dist = stats_service.get_wrong_book_distribution(db, student.id)
    radar = stats_service.get_radar_data(db, student.id)
    heatmap = stats_service.get_heatmap_data(db, student.id)
    subject_time = stats_service.get_subject_time_distribution(db, student.id)

    return {
        "code": 200,
        "data": {
            "student": {"id": student.id, "nickname": student.nickname, "grade": student.grade},
            "time_trend": time_trend,
            "accuracy_by_subject": accuracy_by_subject,
            "wrong_distribution": wrong_dist,
            "radar": radar,
            "heatmap": heatmap,
            "subject_time_distribution": subject_time,
        },
    }


@router.get("/students/{student_id}/plan")
def get_student_plan(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生当前学习计划（只读）"""
    student = _check_observer(db, current_user, student_id)

    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == student.id, StudyPlan.is_active == True
    ).first()
    if not plan:
        return {"code": 200, "data": None}

    today = date.today()
    tasks = db.query(PlanTask).filter(
        PlanTask.plan_id == plan.id,
        PlanTask.date >= today,
        PlanTask.date <= today + timedelta(days=7),
    ).order_by(PlanTask.date, PlanTask.order_num).all()

    tasks_by_date: dict = {}
    for task in tasks:
        key = str(task.date)
        if key not in tasks_by_date:
            tasks_by_date[key] = []
        tasks_by_date[key].append({
            "id": task.id,
            "subject": task.subject,
            "topic": task.topic,
            "task_type": task.task_type,
            "duration_minutes": task.duration_minutes,
            "is_done": task.is_done,
        })

    return {
        "code": 200,
        "data": {
            "plan_id": plan.id,
            "start_date": str(plan.start_date),
            "end_date": str(plan.exam_date),
            "tasks_by_date": tasks_by_date,
        },
    }


@router.post("/students/{student_id}/report")
async def generate_student_report(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为学生生成AI学习报告（流式，教师/家长触发）"""
    student = _check_observer(db, current_user, student_id)

    # 收集近30天数据
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    total_minutes = db.query(func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == student.id,
        StudyLog.date >= thirty_days_ago,
    ).scalar() or 0

    total_days = db.query(func.count(func.distinct(StudyLog.date))).filter(
        StudyLog.user_id == student.id,
        StudyLog.date >= thirty_days_ago,
    ).scalar() or 0

    total_questions = db.query(func.count(QuizAnswer.id)).filter(
        QuizAnswer.user_id == student.id,
    ).scalar() or 0

    avg_accuracy = db.query(func.avg(
        func.case((QuizAnswer.is_correct == True, 1.0), else_=0.0)
    )).filter(QuizAnswer.user_id == student.id).scalar() or 0.0

    accuracy_by_subject = stats_service.get_accuracy_by_subject(db, student.id)
    subject_time = stats_service.get_subject_time_distribution(db, student.id)

    wrong_count = db.query(WrongItem).filter(WrongItem.user_id == student.id).count()
    mastered_count = db.query(WrongItem).filter(
        WrongItem.user_id == student.id, WrongItem.mastery == "mastered"
    ).count()

    streak = stats_service.get_streak_days(db, student.id)
    pomodoro_count = db.query(Pomodoro).filter(
        Pomodoro.user_id == student.id,
        Pomodoro.completed == True,
    ).count()

    stats_30d = {
        "total_study_days": total_days,
        "total_study_minutes": total_minutes,
        "total_questions": total_questions,
        "average_accuracy": round(float(avg_accuracy), 2),
        "accuracy_by_subject": accuracy_by_subject,
        "time_by_subject": subject_time,
        "wrong_book_count": wrong_count,
        "mastered_count": mastered_count,
        "streak_days": streak,
        "pomodoro_count": pomodoro_count,
    }

    student_info = {"nickname": student.nickname, "grade": student.grade}

    async def event_stream():
        async for chunk in ai_service.generate_study_report(student_info, stats_30d):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
