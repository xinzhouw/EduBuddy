from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.document import StudyLog
from app.models.quiz import QuizAnswer, Question
from app.models.wrong_item import WrongItem
from app.models.study_plan import StudyPlan, PlanTask, Pomodoro


def get_today_study_minutes(db: Session, user_id: int) -> int:
    today = date.today()
    result = db.query(func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == user_id,
        StudyLog.date == today,
    ).scalar()
    return result or 0


def get_streak_days(db: Session, user_id: int) -> int:
    """计算连续学习天数"""
    streak = 0
    check_date = date.today()
    while True:
        exists = db.query(StudyLog).filter(
            StudyLog.user_id == user_id,
            StudyLog.date == check_date,
        ).first()
        if exists:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


def get_total_study_days(db: Session, user_id: int) -> int:
    result = db.query(func.count(func.distinct(StudyLog.date))).filter(
        StudyLog.user_id == user_id,
    ).scalar()
    return result or 0


def get_total_questions_done(db: Session, user_id: int) -> int:
    result = db.query(func.count(QuizAnswer.id)).filter(
        QuizAnswer.user_id == user_id,
    ).scalar()
    return result or 0


def get_average_accuracy(db: Session, user_id: int) -> float:
    result = db.query(func.avg(
        case((QuizAnswer.is_correct == True, 1.0), else_=0.0)
    )).filter(QuizAnswer.user_id == user_id).scalar()
    return round(result or 0.0, 2)


def get_study_time_trend(db: Session, user_id: int, period: str) -> dict:
    days = 7 if period == "week" else 30
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    logs = db.query(StudyLog.date, func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == user_id,
        StudyLog.date >= start_date,
        StudyLog.date <= end_date,
    ).group_by(StudyLog.date).all()

    log_map = {str(log[0]): log[1] for log in logs}
    labels = []
    values = []
    current = start_date
    while current <= end_date:
        date_str = str(current)
        labels.append(f"{current.month}/{current.day}")
        values.append(log_map.get(date_str, 0))
        current += timedelta(days=1)

    # 计划目标线（每日应学时长）
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id, StudyPlan.is_active == True
    ).first()
    daily_target = int((plan.daily_hours * 60) if plan else 0)
    targets = [daily_target] * len(labels)

    return {"labels": labels, "values": values, "targets": targets}


def get_accuracy_by_subject(db: Session, user_id: int) -> list:
    results = db.query(
        Question.subject,
        func.count(QuizAnswer.id).label("question_count"),
        func.avg(case((QuizAnswer.is_correct == True, 1.0), else_=0.0)).label("accuracy"),
    ).join(Question, QuizAnswer.question_id == Question.id).filter(
        QuizAnswer.user_id == user_id,
    ).group_by(Question.subject).all()

    return [
        {
            "subject": r.subject,
            "accuracy": round(r.accuracy or 0.0, 2),
            "question_count": r.question_count,
        }
        for r in results
    ]


def get_wrong_book_distribution(db: Session, user_id: int) -> list:
    results = db.query(
        WrongItem.subject,
        func.count(WrongItem.id).label("count"),
    ).filter(
        WrongItem.user_id == user_id,
        WrongItem.mastery != "mastered",
    ).group_by(WrongItem.subject).all()

    return [{"subject": r.subject, "count": r.count} for r in results]


def get_radar_data(db: Session, user_id: int) -> list:
    """各学科掌握深度雷达图数据
    掌握深度 = 正确率(40%) + 复习完成率(30%) + 知识点覆盖率(30%)
    此处简化：正确率(60%) + 错题掌握率(40%)
    """
    SUBJECTS = ["数学", "物理", "化学", "生物", "语文", "英语", "历史", "地理", "政治"]
    result = []

    for subject in SUBJECTS:
        # 该学科正确率
        acc_result = db.query(
            func.avg(case((QuizAnswer.is_correct == True, 1.0), else_=0.0))
        ).join(Question, QuizAnswer.question_id == Question.id).filter(
            QuizAnswer.user_id == user_id,
            Question.subject == subject,
        ).scalar()
        accuracy = float(acc_result or 0.0)

        # 该学科错题掌握率
        total_wrong = db.query(func.count(WrongItem.id)).filter(
            WrongItem.user_id == user_id,
            WrongItem.subject == subject,
        ).scalar() or 0
        mastered_wrong = db.query(func.count(WrongItem.id)).filter(
            WrongItem.user_id == user_id,
            WrongItem.subject == subject,
            WrongItem.mastery == "mastered",
        ).scalar() or 0
        mastery_rate = mastered_wrong / total_wrong if total_wrong > 0 else 0.0

        # 综合评分（0~100）
        score = round((accuracy * 0.6 + mastery_rate * 0.4) * 100, 1)

        result.append({
            "subject": subject,
            "score": score,
            "accuracy": round(accuracy * 100, 1),
            "mastery_rate": round(mastery_rate * 100, 1),
        })

    return result


def get_heatmap_data(db: Session, user_id: int) -> list:
    """近3个月学习活跃度热力图数据"""
    today = date.today()
    ninety_days_ago = today - timedelta(days=89)

    logs = db.query(StudyLog.date, func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == user_id,
        StudyLog.date >= ninety_days_ago,
        StudyLog.date <= today,
    ).group_by(StudyLog.date).all()

    log_map = {str(log[0]): log[1] for log in logs}
    result = []
    current = ninety_days_ago
    while current <= today:
        minutes = log_map.get(str(current), 0)
        # 等级：0=无, 1=1~30min, 2=31~60min, 3=60+min
        if minutes == 0:
            level = 0
        elif minutes <= 30:
            level = 1
        elif minutes <= 60:
            level = 2
        else:
            level = 3
        result.append({
            "date": str(current),
            "minutes": minutes,
            "level": level,
        })
        current += timedelta(days=1)

    return result


def get_subject_time_distribution(db: Session, user_id: int) -> list:
    """近30天各学科学习时长占比"""
    today = date.today()
    thirty_days_ago = today - timedelta(days=29)

    results = db.query(
        StudyLog.subject,
        func.sum(StudyLog.duration_minutes).label("total_minutes"),
    ).filter(
        StudyLog.user_id == user_id,
        StudyLog.date >= thirty_days_ago,
        StudyLog.date <= today,
        StudyLog.subject != None,
    ).group_by(StudyLog.subject).all()

    return [
        {"subject": r.subject, "total_minutes": r.total_minutes}
        for r in results
        if r.subject
    ]


def get_plan_completion_stats(db: Session, user_id: int) -> dict:
    """获取计划完成率统计"""
    today = date.today()

    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id, StudyPlan.is_active == True
    ).first()
    if not plan:
        return {
            "today_completion": 0.0,
            "overall_completion": 0.0,
            "today_done": 0,
            "today_total": 0,
        }

    # 今日完成率
    today_tasks = db.query(PlanTask).filter(
        PlanTask.plan_id == plan.id, PlanTask.date == today
    ).all()
    today_done = sum(1 for t in today_tasks if t.is_done)
    today_total = len(today_tasks)
    today_completion = round(today_done / today_total, 2) if today_total > 0 else 0.0

    # 整体完成率（截至今日）
    all_tasks_due = db.query(PlanTask).filter(
        PlanTask.plan_id == plan.id,
        PlanTask.date <= today,
    ).all()
    all_done = sum(1 for t in all_tasks_due if t.is_done)
    all_total = len(all_tasks_due)
    overall_completion = round(all_done / all_total, 2) if all_total > 0 else 0.0

    return {
        "today_completion": today_completion,
        "overall_completion": overall_completion,
        "today_done": today_done,
        "today_total": today_total,
    }


def get_mastery_score(db: Session, user_id: int, subject: str) -> float:
    """计算某学科的综合掌握深度评分（0~100）"""
    # 正确率
    acc = db.query(
        func.avg(case((QuizAnswer.is_correct == True, 1.0), else_=0.0))
    ).join(Question, QuizAnswer.question_id == Question.id).filter(
        QuizAnswer.user_id == user_id,
        Question.subject == subject,
    ).scalar() or 0.0

    # 错题掌握率
    total_wrong = db.query(func.count(WrongItem.id)).filter(
        WrongItem.user_id == user_id, WrongItem.subject == subject
    ).scalar() or 0
    mastered = db.query(func.count(WrongItem.id)).filter(
        WrongItem.user_id == user_id,
        WrongItem.subject == subject,
        WrongItem.mastery == "mastered",
    ).scalar() or 0
    mastery_rate = mastered / total_wrong if total_wrong > 0 else 0.0

    return round((float(acc) * 0.6 + mastery_rate * 0.4) * 100, 1)
