import json
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.wrong_item import WrongItem, WrongReview
from app.schemas.wrong_item import WrongItemCreate, WrongItemOut, MasteryUpdate, ReviewSubmit, ReviewResult
from app.services.ai_service import ai_service
from app.services.review_service import get_next_review_date, get_initial_review_date, get_review_message

router = APIRouter(prefix="/api/wrong-book", tags=["错题本"])


@router.get("")
def list_wrong_items(
    subject: Optional[str] = None,
    mastery: Optional[str] = None,
    due_review: Optional[bool] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WrongItem).filter(WrongItem.user_id == current_user.id)
    if subject:
        query = query.filter(WrongItem.subject == subject)
    if mastery:
        query = query.filter(WrongItem.mastery == mastery)
    if due_review:
        today = date.today()
        query = query.filter(WrongItem.next_review_at <= today, WrongItem.mastery != "mastered")

    total = query.count()
    today_due = db.query(WrongItem).filter(
        WrongItem.user_id == current_user.id,
        WrongItem.next_review_at <= date.today(),
        WrongItem.mastery != "mastered",
    ).count()

    items = query.order_by(WrongItem.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {"code": 200, "data": {
        "items": [WrongItemOut.model_validate(i) for i in items],
        "total": total,
        "today_due_count": today_due,
    }}


@router.post("")
def create_wrong_item(
    data: WrongItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = WrongItem(
        user_id=current_user.id,
        question=data.question,
        correct_answer=data.correct_answer,
        user_wrong_answer=data.user_wrong_answer,
        subject=data.subject,
        tags=json.dumps(data.tags, ensure_ascii=False),
        source="manual",
        next_review_at=get_initial_review_date(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"code": 200, "data": WrongItemOut.model_validate(item)}


@router.get("/{item_id}")
def get_wrong_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(WrongItem).filter(WrongItem.id == item_id, WrongItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="错题不存在")
    return {"code": 200, "data": WrongItemOut.model_validate(item)}


@router.post("/{item_id}/ai-explain")
async def ai_explain(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(WrongItem).filter(WrongItem.id == item_id, WrongItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="错题不存在")

    full_response = []

    async def generate():
        async for chunk in ai_service.explain_wrong_answer(
            question=item.question,
            correct_answer=item.correct_answer,
            wrong_answer=item.user_wrong_answer,
        ):
            full_response.append(chunk)
            yield f"data: {json.dumps({'type': 'content', 'delta': chunk}, ensure_ascii=False)}\n\n"

        full_content = "".join(full_response)
        item.ai_explanation = full_content
        db.commit()
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/{item_id}/follow-up")
async def follow_up(
    item_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(WrongItem).filter(WrongItem.id == item_id, WrongItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="错题不存在")
    question = data.get("question", "")

    async def generate():
        async for chunk in ai_service.follow_up_stream(
            question=question,
            context=item.ai_explanation or "",
        ):
            yield f"data: {json.dumps({'type': 'content', 'delta': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.put("/{item_id}/mastery")
def update_mastery(
    item_id: int,
    data: MasteryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(WrongItem).filter(WrongItem.id == item_id, WrongItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="错题不存在")
    item.mastery = data.mastery
    db.commit()
    return {"code": 200, "message": "掌握程度已更新"}


@router.post("/{item_id}/review")
def review_item(
    item_id: int,
    data: ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(WrongItem).filter(WrongItem.id == item_id, WrongItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="错题不存在")

    # 记录复习
    review = WrongReview(
        wrong_item_id=item_id,
        user_id=current_user.id,
        user_answer=data.answer,
        is_correct=data.is_correct,
    )
    db.add(review)

    # 更新下次复习时间和掌握程度
    new_review_count = item.review_count + (1 if data.is_correct else 0)
    next_review, mastery = get_next_review_date(new_review_count, data.is_correct)
    item.review_count = new_review_count if data.is_correct else 0
    item.next_review_at = next_review
    item.mastery = mastery
    db.commit()

    message = get_review_message(next_review, item.review_count, mastery, data.is_correct)
    return {"code": 200, "data": ReviewResult(
        next_review_at=next_review,
        review_count=item.review_count,
        mastery=mastery,
        message=message,
    )}


@router.delete("/{item_id}")
def delete_wrong_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(WrongItem).filter(WrongItem.id == item_id, WrongItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="错题不存在")
    db.delete(item)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.post("/{item_id}/similar-quiz")
async def similar_quiz(
    item_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(WrongItem).filter(WrongItem.id == item_id, WrongItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="错题不存在")
    count = data.get("count", 3)
    tags = json.loads(item.tags) if item.tags else []
    topic = tags[0] if tags else item.subject

    questions = await ai_service.generate_quiz(
        subject=item.subject,
        topic=topic,
        difficulty=2,
        question_types=["single_choice", "fill_blank"],
        count=count,
        grade=current_user.grade,
    )
    return {"code": 200, "data": {"questions": questions}}
