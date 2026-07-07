import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Query, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.note import ChatSession, ChatMessage
from app.models.wrong_item import WrongItem
from app.models.image import ChatImage
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service
from app.services.image_service import image_service
from app.services.meta_service import meta_service, build_meta_context
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
    session_id: Optional[str] = Form(None),
    question: str = Form(...),
    subject: str = Form("数学"),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI 问答（支持图片上传）

    请求：multipart/form-data
    - session_id: 会话 ID（可选）
    - question: 问题文本
    - subject: 学科
    - images: 图片文件数组（最多 5 张）
    """
    # 1. 验证和保存图片
    image_objs = []
    if images:
        try:
            valid, error = await image_service.validate_files(images)
            if not valid:
                raise HTTPException(status_code=400, detail=error)

            if not session_id:
                session_id = str(uuid.uuid4())

            image_ids = await image_service.save_images(images, current_user.id, session_id, db)
            image_objs = db.query(ChatImage).filter(ChatImage.id.in_(image_ids)).all()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"图片保存失败: {str(e)}")

    # 2. 获取或创建会话
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session_id = str(uuid.uuid4())
        title = question[:50] if len(question) > 0 else "新对话"
        session = ChatSession(id=session_id, user_id=current_user.id, title=title, subject=subject)
        db.add(session)
        db.commit()

    # 3. 获取历史消息（最近10条）
    history_msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).limit(10).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]

    # 4. 保存用户消息（含图片）
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=question,
        image_ids=json.dumps([img.id for img in image_objs]) if image_objs else None,
    )
    db.add(user_msg)
    db.commit()

    # 5. 读取用户信息（避免 DetachedInstanceError）
    user_id = current_user.id
    user_grade = current_user.grade

    # 6. 构建上下文
    meta_context = build_meta_context(
        question=question,
        subject=subject if subject != "全部" else None,
        grade=user_grade if user_grade else None,
    )

    rag_context = rag_service.build_context_prompt(
        query=question,
        subject=subject if subject != "全部" else None,
        grade=user_grade if user_grade else None,
        top_k=4,
    )

    combined_context = (meta_context or "") + (rag_context or "")


    # 7. 流式对话（如有图片则使用增强版本）
    full_response = []
    message_id_holder = []

    async def generate():
        if image_objs:
            async for chunk in ai_service.chat_stream_with_images(
                question=question,
                subject=subject,
                grade=user_grade,
                images=image_objs,
                history=history,
                rag_context=combined_context,
            ):
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk}, ensure_ascii=False)}\n\n"
        else:
            async for chunk in ai_service.chat_stream(
                question=question,
                subject=subject,
                grade=user_grade,
                history=history,
                rag_context=combined_context,
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
    from sqlalchemy import func, desc

    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
    total = query.count()
    sessions = query.order_by(ChatSession.updated_at.desc()).offset((page - 1) * size).limit(size).all()

    # 构建会话 ID 列表
    session_ids = [s.id for s in sessions]

    # 一次查询获取每个会话的消息统计 + 最后消息时间
    msg_stats = db.query(
        ChatMessage.session_id,
        func.count(ChatMessage.id).label("msg_count"),
        func.max(ChatMessage.created_at).label("last_msg_time")
    ).filter(ChatMessage.session_id.in_(session_ids)).group_by(ChatMessage.session_id).all()

    stats_map = {stat[0]: {"count": stat[1], "last_time": stat[2]} for stat in msg_stats}

    items = []
    for s in sessions:
        stat = stats_map.get(s.id, {"count": 0, "last_time": None})
        items.append({
            "id": s.id,
            "title": s.title,
            "subject": s.subject,
            "last_message_at": stat["last_time"].isoformat() if stat["last_time"] else s.created_at.isoformat(),
            "message_count": stat["count"],
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


@router.get("/knowledge-base/stats")
def get_knowledge_base_stats(
    current_user: User = Depends(get_current_user),
):
    """
    查询教材知识库状态（是否可用、已索引教材数量等）
    """
    stats = rag_service.get_stats()
    return {"code": 200, "data": stats}


@router.get("/knowledge-base/retrieve")
async def retrieve_from_knowledge_base(
    query: str = Query(..., description="查询内容"),
    subject: Optional[str] = Query(None, description="学科过滤（如：数学、物理）"),
    top_k: int = Query(4, ge=1, le=10, description="返回条数"),
    current_user: User = Depends(get_current_user),
):
    """
    直接从教材知识库检索相关内容（调试/预览用）
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    results = rag_service.retrieve(query=query.strip(), subject=subject, top_k=top_k)
    return {
        "code": 200,
        "data": {
            "query": query,
            "rag_available": rag_service.is_available,
            "results": results,
        }
    }


@router.get("/chat/{session_id}/images")
def get_session_images(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话中的所有图片"""
    from app.schemas.image import ImageResponse

    # 验证会话属主
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 查询图片（排除已软删除的）
    images = db.query(ChatImage).filter(
        ChatImage.session_id == session_id,
        ChatImage.deleted_at.is_(None),
    ).order_by(ChatImage.created_at.desc()).all()

    return {
        "code": 200,
        "data": [ImageResponse.model_validate(img).model_dump(mode="json") for img in images],
    }


@router.delete("/chat/images/{image_id}")
def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除图片（需权限检查）"""
    from datetime import datetime
    import os
    from app.config import get_settings

    image = db.query(ChatImage).filter(ChatImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 权限检查：只能删除自己的图片
    if image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除他人的图片")

    # 软删除数据库记录
    image.deleted_at = datetime.utcnow()
    db.commit()

    # 同时删除磁盘上的文件
    upload_dir = get_settings().upload_dir or "./uploads"
    file_path = os.path.join(upload_dir, image.file_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"删除文件失败: {e}")

    return {"code": 200, "message": "图片已删除"}
