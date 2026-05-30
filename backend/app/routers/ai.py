import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.note import ChatSession, ChatMessage
from app.models.wrong_item import WrongItem
from app.services.ai_service import ai_service
from app.services.review_service import get_initial_review_date

router = APIRouter(prefix="/api/ai", tags=["AI问答"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    question: str
    subject: str = "数学"
    images: List[str] = []


class FeedbackRequest(BaseModel):
    rating: str  # 'thumbs_up' / 'thumbs_down'
    reason: Optional[str] = None


class AddToWrongBookRequest(BaseModel):
    subject: str
    tags: List[str] = []


@router.post("/chat")
async def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 获取或创建会话
    session_id = data.session_id
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session_id = str(uuid.uuid4())
        title = data.question[:50] if len(data.question) > 0 else "新对话"
        session = ChatSession(id=session_id, user_id=current_user.id, title=title, subject=data.subject)
        db.add(session)
        db.commit()

    # 获取历史消息（最近10条）
    history_msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
    history = [{"role": m.role, "content": m.content} for m in reversed(history_msgs)]

    # 保存用户消息
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=data.question,
    )
    db.add(user_msg)
    db.commit()

    # 提前读取 current_user 的属性，避免 StreamingResponse 中 Session 关闭后 DetachedInstanceError
    user_id = current_user.id
    user_grade = current_user.grade

    # 收集完整回复以便保存
    full_response = []
    message_id_holder = []

    async def generate():
        async for chunk in ai_service.chat_stream(
            question=data.question,
            subject=data.subject,
            grade=user_grade,
            history=history,
        ):
            full_response.append(chunk)
            yield f"data: {json.dumps({'type': 'content', 'delta': chunk}, ensure_ascii=False)}\n\n"

        # 保存AI回复
        full_content = "".join(full_response)
        ai_msg = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=full_content,
        )
        db.add(ai_msg)
        # 更新会话时间
        from sqlalchemy.sql import func
        session.updated_at = func.now()
        db.commit()
        db.refresh(ai_msg)
        message_id_holder.append(ai_msg.id)

        yield f"data: {json.dumps({'type': 'done', 'message_id': ai_msg.id, 'session_id': session_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions")
def get_sessions(
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
    total = query.count()
    sessions = query.order_by(ChatSession.updated_at.desc()).offset((page - 1) * size).limit(size).all()

    items = []
    for s in sessions:
        msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        last_msg = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).order_by(ChatMessage.created_at.desc()).first()
        items.append({
            "id": s.id,
            "title": s.title,
            "subject": s.subject,
            "last_message_at": last_msg.created_at.isoformat() if last_msg else s.created_at.isoformat(),
            "message_count": msg_count,
        })

    return {"code": 200, "data": {"items": items, "total": total, "page": page, "size": size}}


@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()

    return {"code": 200, "data": [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "feedback": m.feedback,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]}


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    # 删除该会话下的所有消息
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"code": 200, "message": "会话已删除"}


@router.post("/messages/{message_id}/feedback")
def feedback(
    message_id: int,
    data: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(ChatMessage).filter(
        ChatMessage.id == message_id, ChatMessage.user_id == current_user.id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    msg.feedback = data.rating
    msg.feedback_reason = data.reason
    db.commit()
    return {"code": 200, "message": "反馈已记录"}


@router.post("/messages/{message_id}/add-to-wrong-book")
def add_to_wrong_book(
    message_id: int,
    data: AddToWrongBookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(ChatMessage).filter(
        ChatMessage.id == message_id, ChatMessage.user_id == current_user.id, ChatMessage.role == "user"
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    # 获取对应的AI回复
    ai_msg = db.query(ChatMessage).filter(
        ChatMessage.session_id == msg.session_id,
        ChatMessage.role == "assistant",
        ChatMessage.id > message_id,
    ).first()

    item = WrongItem(
        user_id=current_user.id,
        question=msg.content,
        correct_answer=ai_msg.content if ai_msg else "（请查看AI解析）",
        subject=data.subject,
        tags=json.dumps(data.tags, ensure_ascii=False),
        source="ai_chat",
        source_id=str(message_id),
        next_review_at=get_initial_review_date(),
    )
    db.add(item)
    db.commit()
    return {"code": 200, "message": "已加入错题本"}
