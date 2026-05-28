import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.quiz import QuizSession, Question, QuizAnswer
from app.models.wrong_item import WrongItem
from app.schemas.quiz import QuizGenerateRequest, QuizSubmitRequest, AnswerResult, QuizResult
from app.services.ai_service import ai_service
from app.services.review_service import get_initial_review_date

router = APIRouter(prefix="/api/quiz", tags=["练习题"])


@router.post("/generate")
async def generate_quiz(
    data: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    questions_data = await ai_service.generate_quiz(
        subject=data.subject,
        topic=data.topic,
        difficulty=data.difficulty,
        question_types=data.question_types,
        count=data.count,
        grade=current_user.grade,
    )

    session_id = str(uuid.uuid4())
    session = QuizSession(
        id=session_id,
        user_id=current_user.id,
        subject=data.subject,
        topic=data.topic,
        difficulty=data.difficulty,
        question_types=json.dumps(data.question_types, ensure_ascii=False),
        total_count=len(questions_data),
    )
    db.add(session)

    questions_out = []
    for i, q in enumerate(questions_data):
        question = Question(
            session_id=session_id,
            question_type=q.get("type", "single_choice"),
            content=q.get("content", ""),
            options=json.dumps(q.get("options"), ensure_ascii=False) if q.get("options") else None,
            correct_answer=q.get("correct_answer", ""),
            explanation=q.get("explanation", ""),
            difficulty=data.difficulty,
            subject=data.subject,
            topic=data.topic,
            order_num=i + 1,
        )
        db.add(question)
        db.flush()
        questions_out.append({
            "id": question.id,
            "type": question.question_type,
            "content": question.content,
            "options": q.get("options"),
            "difficulty": question.difficulty,
        })
    db.commit()
    return {"code": 200, "data": {"session_id": session_id, "questions": questions_out}}


@router.post("/sessions/{session_id}/submit")
async def submit_quiz(
    session_id: str,
    data: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(QuizSession).filter(
        QuizSession.id == session_id, QuizSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="练习会话不存在")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="练习已提交")

    results = []
    correct_count = 0
    total_time = 0
    wrong_item_ids = []

    for ans in data.answers:
        question = db.query(Question).filter(Question.id == ans.question_id, Question.session_id == session_id).first()
        if not question:
            continue
        is_correct = ans.answer.strip().upper() == question.correct_answer.strip().upper()
        if is_correct:
            correct_count += 1
        total_time += ans.time_spent

        qa = QuizAnswer(
            session_id=session_id,
            question_id=ans.question_id,
            user_id=current_user.id,
            user_answer=ans.answer,
            is_correct=is_correct,
            time_spent=ans.time_spent,
        )
        db.add(qa)

        # 错题自动录入
        if not is_correct:
            item = WrongItem(
                user_id=current_user.id,
                question=question.content,
                correct_answer=question.correct_answer,
                user_wrong_answer=ans.answer,
                subject=question.subject,
                tags=json.dumps([question.topic], ensure_ascii=False),
                source="quiz",
                source_id=str(ans.question_id),
                next_review_at=get_initial_review_date(),
                ai_explanation=question.explanation,
            )
            db.add(item)
            db.flush()
            wrong_item_ids.append(item.id)

        results.append(AnswerResult(
            question_id=ans.question_id,
            is_correct=is_correct,
            correct_answer=question.correct_answer,
            user_answer=ans.answer,
            explanation=question.explanation,
        ))

    # 更新会话状态
    session.correct_count = correct_count
    session.time_spent = total_time
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    db.commit()

    accuracy = correct_count / len(data.answers) if data.answers else 0
    return {"code": 200, "data": QuizResult(
        total=len(data.answers),
        correct=correct_count,
        accuracy=round(accuracy, 2),
        time_spent=total_time,
        results=results,
        wrong_items_added=wrong_item_ids,
    )}


@router.get("/sessions")
def list_sessions(
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(QuizSession).filter(
        QuizSession.user_id == current_user.id, QuizSession.status == "completed"
    )
    total = query.count()
    sessions = query.order_by(QuizSession.created_at.desc()).offset((page - 1) * size).limit(size).all()
    items = []
    for s in sessions:
        accuracy = s.correct_count / s.total_count if s.total_count > 0 else 0
        items.append({
            "id": s.id,
            "subject": s.subject,
            "topic": s.topic,
            "total": s.total_count,
            "correct": s.correct_count,
            "accuracy": round(accuracy, 2),
            "created_at": s.created_at.isoformat(),
        })
    return {"code": 200, "data": {"items": items, "total": total}}


@router.get("/recommended-difficulty")
def recommended_difficulty(
    subject: str,
    topic: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func, case
    result = db.query(
        func.avg(case((QuizAnswer.is_correct == True, 1.0), else_=0.0))
    ).join(Question, QuizAnswer.question_id == Question.id).filter(
        QuizAnswer.user_id == current_user.id,
        Question.subject == subject,
        Question.topic == topic,
    ).scalar()

    accuracy = result or 0.0
    if accuracy > 0.8:
        difficulty = 3
        reason = f"您在该知识点的历史正确率为{int(accuracy*100)}%，推荐困难难度"
    elif accuracy >= 0.4:
        difficulty = 2
        reason = f"您在该知识点的历史正确率为{int(accuracy*100)}%，推荐中等难度"
    else:
        difficulty = 1
        reason = f"您在该知识点的历史正确率为{int(accuracy*100)}%，推荐基础难度"

    return {"code": 200, "data": {
        "recommended_difficulty": difficulty,
        "reason": reason,
        "accuracy_history": round(accuracy, 2),
    }}
