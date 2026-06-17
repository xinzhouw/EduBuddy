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
    """计算连续学习天数 - 使用 SQL 窗口函数，避免 O(N) 循环"""
    today = date.today()
    # 查询最近 180 天的学习日期，按倒序排列
    recent_logs = db.query(func.distinct(StudyLog.date)).filter(
        StudyLog.user_id == user_id,
        StudyLog.date <= today,
        StudyLog.date >= today - timedelta(days=180)
    ).order_by(StudyLog.date.desc()).all()

    if not recent_logs:
        return 0

    # 从今天开始，向后遍历连续天数
    streak = 0
    expected_date = today
    for log_date_tuple in recent_logs:
        log_date = log_date_tuple[0]
        if log_date == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        elif log_date < expected_date:
            # 出现日期间隙，streaks 中断
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
    """各学科掌握深度雷达图数据 - 使用 GROUP BY 聚合，减少从 27 个查询到 3 个
    掌握深度 = 正确率(60%) + 错题掌握率(40%)
    """
    SUBJECTS = ["数学", "物理", "化学", "生物", "语文", "英语", "历史", "地理", "政治"]

    # 查询 1：按学科聚合正确率
    accuracy_data = db.query(
        Question.subject,
        func.avg(case((QuizAnswer.is_correct == True, 1.0), else_=0.0)).label("accuracy")
    ).join(Question, QuizAnswer.question_id == Question.id).filter(
        QuizAnswer.user_id == user_id,
    ).group_by(Question.subject).all()
    accuracy_map = {r.subject: float(r.accuracy or 0.0) for r in accuracy_data}

    # 查询 2：按学科统计总错题数
    total_wrong_data = db.query(
        WrongItem.subject,
        func.count(WrongItem.id).label("count")
    ).filter(
        WrongItem.user_id == user_id,
    ).group_by(WrongItem.subject).all()
    total_wrong_map = {r.subject: r.count for r in total_wrong_data}

    # 查询 3：按学科统计已掌握错题数
    mastered_data = db.query(
        WrongItem.subject,
        func.count(WrongItem.id).label("count")
    ).filter(
        WrongItem.user_id == user_id,
        WrongItem.mastery == "mastered",
    ).group_by(WrongItem.subject).all()
    mastered_map = {r.subject: r.count for r in mastered_data}

    result = []
    for subject in SUBJECTS:
        accuracy = accuracy_map.get(subject, 0.0)
        total_wrong = total_wrong_map.get(subject, 0)
        mastered_wrong = mastered_map.get(subject, 0)
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

    # 今日完成率 - 使用 SQL COUNT，避免加载所有行到 Python
    today_total = db.query(func.count(PlanTask.id)).filter(
        PlanTask.plan_id == plan.id, PlanTask.date == today
    ).scalar() or 0
    today_done = db.query(func.count(PlanTask.id)).filter(
        PlanTask.plan_id == plan.id,
        PlanTask.date == today,
        PlanTask.is_done == True,
    ).scalar() or 0
    today_completion = round(today_done / today_total, 2) if today_total > 0 else 0.0

    # 整体完成率（截至今日）- 使用 SQL COUNT
    all_total = db.query(func.count(PlanTask.id)).filter(
        PlanTask.plan_id == plan.id,
        PlanTask.date <= today,
    ).scalar() or 0
    all_done = db.query(func.count(PlanTask.id)).filter(
        PlanTask.plan_id == plan.id,
        PlanTask.date <= today,
        PlanTask.is_done == True,
    ).scalar() or 0
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
