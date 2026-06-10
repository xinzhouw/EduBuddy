import json
import random
import string
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.advice import DailyAdvice, AdviceAction
from app.models.wrong_item import WrongItem
from app.models.study_plan import PlanTask, StudyPlan
from app.models.document import StudyLog
from app.models.quiz import QuizAnswer, Question
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/advice", tags=["每日建议"])


def _collect_context(db: Session, user: User) -> dict:
    """汇总学生学习数据，用于 AI 生成每日建议"""
    today = date.today()

    # 连续打卡天数
    streak = 0
    check = today
    while True:
        exists = db.query(StudyLog).filter(
            StudyLog.user_id == user.id, StudyLog.date == check
        ).first()
        if exists:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    # 今日计划完成率
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user.id, StudyPlan.is_active == True
    ).first()
    today_completion = 0.0
    if plan:
        tasks_today = db.query(PlanTask).filter(
            PlanTask.plan_id == plan.id, PlanTask.date == today
        ).all()
        if tasks_today:
            done = sum(1 for t in tasks_today if t.is_done)
            today_completion = done / len(tasks_today)

    # 近3天正确率趋势（按天计算）
    accuracy_trend = []
    for i in range(2, -1, -1):
        d = today - timedelta(days=i)
        # 获取该天的答题记录（通过 QuizAnswer 的 created_at 或通过 session 关联）
        # 简化：用近3天整体正确率趋势近似（实际可按天细分）
        res = db.query(
            func.avg(
                case((QuizAnswer.is_correct == True, 1.0), else_=0.0)
            )
        ).filter(
            QuizAnswer.user_id == user.id,
            func.date(QuizAnswer.created_at) == d,
        ).scalar()
        accuracy_trend.append(round(float(res or 0.0), 2))

    # 薄弱学科（错题多且正确率低的）
    wrong_by_subject = db.query(
        WrongItem.subject, func.count(WrongItem.id).label("cnt")
    ).filter(
        WrongItem.user_id == user.id, WrongItem.mastery != "mastered"
    ).group_by(WrongItem.subject).order_by(func.count(WrongItem.id).desc()).limit(3).all()
    weak_subjects = [r.subject for r in wrong_by_subject]

    # 到期复习项（错题中 next_review_at <= today 且未掌握）
    due_reviews_raw = db.query(WrongItem).filter(
        WrongItem.user_id == user.id,
        WrongItem.mastery != "mastered",
        WrongItem.next_review_at <= today,
    ).limit(10).all()
    due_reviews = [
        {
            "subject": w.subject,
            "topic": "",
            "days_since_last_review": (today - w.next_review_at).days if w.next_review_at else 0,
        }
        for w in due_reviews_raw
    ]

    # 近7天建议执行情况
    seven_days_ago = today - timedelta(days=7)
    prev_advices = db.query(DailyAdvice).filter(
        DailyAdvice.user_id == user.id,
        DailyAdvice.date >= seven_days_ago,
        DailyAdvice.date < today,
    ).order_by(DailyAdvice.date.desc()).limit(3).all()

    prev_outcomes = []
    for adv in prev_advices:
        try:
            items = json.loads(adv.advices_json)
        except Exception:
            items = []
        for item in items:
            item_id = item.get("id", "")
            action = db.query(AdviceAction).filter(
                AdviceAction.advice_id == adv.id,
                AdviceAction.advice_item_id == item_id,
            ).first()
            prev_outcomes.append({
                "type": item.get("type"),
                "acted": action is not None,
                "outcome": action.outcome if action else None,
            })

    return {
        "student_info": {"nickname": user.nickname, "grade": user.grade},
        "recent_stats": {
            "streak_days": streak,
            "today_plan_completion": today_completion,
            "recent_accuracy_trend": accuracy_trend,
            "weak_subjects": weak_subjects,
        },
        "due_reviews": due_reviews,
        "previous_advice_outcomes": prev_outcomes,
    }


@router.get("/today")
async def get_today_advice(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取今日建议，若还未生成则触发生成"""
    today = date.today()

    # 查询今日是否已有建议
    existing = db.query(DailyAdvice).filter(
        DailyAdvice.user_id == current_user.id,
        DailyAdvice.date == today,
    ).first()

    is_new = False
    if not existing:
        # 生成新建议
        context = _collect_context(db, current_user)
        try:
            advices = await ai_service.generate_daily_advice(context)
        except Exception:
            advices = []
        if not advices:
            # AI 失败时生成默认建议
            advices = [
                {
                    "id": "adv-default-001",
                    "type": "general",
                    "priority": 1,
                    "icon": "📚",
                    "title": "今日学习加油",
                    "content": "保持每天学习的好习惯，坚持就是胜利！今日计划的任务记得完成哦。",
                    "action": {"label": "查看计划", "route": "/plan", "params": {}},
                    "theory_basis": "间隔效应：分散学习比集中学习记忆保留率更高，每天坚持学习效果最佳。",
                }
            ]
        existing = DailyAdvice(
            user_id=current_user.id,
            date=today,
            advices_json=json.dumps(advices, ensure_ascii=False),
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
        is_new = True

    # 更新 shown_at
    if not existing.shown_at:
        existing.shown_at = datetime.utcnow()
        db.commit()

    try:
        advices_list = json.loads(existing.advices_json)
    except Exception:
        advices_list = []

    return {
        "code": 200,
        "data": {
            "date": str(today),
            "is_new": is_new,
            "advice_id": existing.id,
            "advices": advices_list,
        },
    }


@router.post("/{advice_id}/action")
def record_advice_action(
    advice_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """记录用户对某条建议的执行行为"""
    adv = db.query(DailyAdvice).filter(
        DailyAdvice.id == advice_id,
        DailyAdvice.user_id == current_user.id,
    ).first()
    if not adv:
        raise HTTPException(status_code=404, detail="建议不存在")

    advice_item_id = payload.get("advice_item_id", "")
    action = AdviceAction(
        advice_id=advice_id,
        advice_item_id=advice_item_id,
        user_id=current_user.id,
    )
    db.add(action)
    db.commit()
    return {"code": 200, "message": "已记录"}


@router.get("/history")
def get_advice_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取近7天建议历史"""
    seven_days_ago = date.today() - timedelta(days=7)
    records = db.query(DailyAdvice).filter(
        DailyAdvice.user_id == current_user.id,
        DailyAdvice.date >= seven_days_ago,
    ).order_by(DailyAdvice.date.desc()).all()

    result = []
    for r in records:
        try:
            advices = json.loads(r.advices_json)
        except Exception:
            advices = []
        result.append({
            "id": r.id,
            "date": str(r.date),
            "advices": advices,
            "shown_at": r.shown_at.isoformat() if r.shown_at else None,
        })
    return {"code": 200, "data": result}
