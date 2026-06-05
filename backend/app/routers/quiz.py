import uuid
import json
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
from app.services.document_service import extract_text

router = APIRouter(prefix="/api/quiz", tags=["练习题"])

# 支持上传的图片/文档类型
EXTRACT_SUPPORTED_TYPES = {
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/webp": "image",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


@router.post("/extract-answer")
async def extract_answer_from_image(
    file: UploadFile = File(...),
    question_content: str = Form(""),
    current_user: User = Depends(get_current_user),
):
    """从图片中识别手写/打印的答案内容
    
    支持格式：JPG、PNG、GIF、WebP
    返回：answer（识别到的答案文字）、confidence（识别置信度）
    """
    content_type = file.content_type or ""
    image_types = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
    if content_type not in image_types:
        raise HTTPException(
            status_code=400,
            detail="答案识别仅支持图片格式（JPG、PNG、GIF、WebP）"
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小超过限制（最大 10MB）")

    try:
        image_b64 = base64.b64encode(content).decode("utf-8")
        mime = content_type if content_type.startswith("image/") else "image/jpeg"
        result = await ai_service.extract_answer_from_image(
            image_b64, mime, question_content
        )
        return {"code": 200, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 识别失败：{str(e)}")


@router.post("/extract-topic")
async def extract_topic_from_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """从图片或文档中识别题目，提取学科和知识点
    
    支持格式：JPG、PNG、GIF、WebP（图片通过 Vision API 识别）、PDF、DOCX（文字提取后 AI 分析）
    返回：subject（学科）、topic（知识点）、recognized_text（识别文字）、question_count（题目数）
    """
    content_type = file.content_type or ""
    file_kind = EXTRACT_SUPPORTED_TYPES.get(content_type)
    if not file_kind:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件类型，请上传 JPG、PNG、PDF 或 Word 文件"
        )

    # 读取文件内容
    content = await file.read()
    max_size = 10 * 1024 * 1024  # 10 MB
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="文件大小超过限制（最大 10MB）")

    try:
        if file_kind == "image":
            # 图片：用 Vision API 直接识别
            image_b64 = base64.b64encode(content).decode("utf-8")
            # 标准化 mime type
            mime = content_type if content_type.startswith("image/") else "image/jpeg"
            result = await ai_service.extract_quiz_topic_from_image(image_b64, mime)
        else:
            # PDF / DOCX：先保存到临时文件再提取文字
            import tempfile
            suffix = ".pdf" if file_kind == "pdf" else ".docx"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            extracted = extract_text(tmp_path, file_kind)
            import os
            os.unlink(tmp_path)

            # ── 图片型 PDF 降级：文字层为空时，用 Vision OCR 逐页识别 ──────────
            if file_kind == "pdf" and (not extracted or extracted.startswith("[")):
                try:
                    extracted = await _ocr_pdf_pages_for_quiz(content)
                except Exception as _ocr_e:
                    extracted = f"[扫描版PDF，OCR识别失败：{_ocr_e}]"

            if not extracted or extracted.startswith("["):
                raise HTTPException(status_code=422, detail=f"文件内容提取失败：{extracted}")
            result = await ai_service.extract_quiz_topic_from_pdf(extracted)

        return {"code": 200, "data": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 识别失败：{str(e)}")


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


async def _ocr_pdf_pages_for_quiz(pdf_bytes: bytes) -> str:
    """将扫描版 PDF 每页转换为图片，逐页调用 Vision OCR，拼接返回全文。

    仅在 PDF 文字层为空（扫描/图片型PDF）时调用。
    依赖：PyMuPDF（fitz），容器中已安装。
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = doc.page_count
    all_texts: list[str] = []

    for page_index in range(page_count):
        page = doc[page_index]
        # 渲染为 150 DPI 的 PNG（提高 OCR 精度）
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img_bytes = pix.tobytes("png")
        image_base64 = base64.b64encode(img_bytes).decode("utf-8")

        try:
            result = await ai_service.ocr_image_for_reading(
                image_base64=image_base64,
                mime_type="image/png",
            )
            page_text = result.get("text", "").strip()
        except Exception as e:
            page_text = f"[第 {page_index + 1} 页识别失败：{e}]"

        if page_text:
            all_texts.append(page_text)

    doc.close()
    return "\n\n".join(all_texts)
