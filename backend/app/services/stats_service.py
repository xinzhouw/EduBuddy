from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.document import StudyLog
from app.models.quiz import QuizAnswer, Question, QuizSession
from app.models.wrong_item import WrongItem


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

    return {"labels": labels, "values": values}


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
