import base64
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.homework import HomeworkGrading
from app.services.ai_service import ai_service
from app.services.document_service import save_upload_file, extract_text

router = APIRouter(prefix="/api/homework", tags=["AI批改作业"])

# 支持的文件类型
SUPPORTED_FILE_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}

SUBJECTS = ["数学", "物理", "化学", "生物", "语文", "英语", "历史", "地理", "政治"]


class TextGradingRequest(BaseModel):
    title: str = "我的作业"
    subject: str = "数学"
    grade_level: Optional[str] = None
    content: str


@router.post("/grade/text")
async def grade_text_homework(
    data: TextGradingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交文本作业进行 AI 批改（流式返回）"""
    if data.subject not in SUBJECTS:
        raise HTTPException(status_code=400, detail=f"不支持的学科，请选择：{', '.join(SUBJECTS)}")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="作业内容不能为空")
    if len(data.content) > 10000:
        raise HTTPException(status_code=400, detail="作业内容过长，请控制在10000字以内")

    # 创建批改记录
    grading = HomeworkGrading(
        user_id=current_user.id,
        title=data.title or "我的作业",
        subject=data.subject,
        grade_level=data.grade_level or current_user.grade,
        content_type="text",
        content_text=data.content,
        status="processing",
    )
    db.add(grading)
    db.commit()
    db.refresh(grading)
    grading_id = grading.id

    # 提前读取用户年级避免 Session 关闭后访问
    grade_level = data.grade_level or current_user.grade or ""

    full_report = []

    async def generate():
        try:
            async for chunk in ai_service.grade_homework(
                subject=data.subject,
                grade_level=grade_level,
                content=data.content,
            ):
                full_report.append(chunk)
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk}, ensure_ascii=False)}\n\n"

            # 批改完成，保存结果
            report_text = "".join(full_report)
            score = await ai_service.extract_score_from_report(report_text)

            record = db.query(HomeworkGrading).filter(HomeworkGrading.id == grading_id).first()
            if record:
                record.status = "done"
                record.detailed_feedback = report_text
                record.score = score
                record.graded_at = datetime.utcnow()
                db.commit()

            yield f"data: {json.dumps({'type': 'done', 'grading_id': grading_id, 'score': score}, ensure_ascii=False)}\n\n"

        except Exception as e:
            # 标记为错误状态
            record = db.query(HomeworkGrading).filter(HomeworkGrading.id == grading_id).first()
            if record:
                record.status = "error"
                db.commit()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/recognize")
async def recognize_homework_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """识别图片中的作业文字内容（预览用，不保存记录）"""
    content_type = file.content_type or ""
    is_image = content_type in {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
    if not is_image:
        raise HTTPException(status_code=400, detail="仅支持图片文件（JPG/PNG/GIF/WebP）")

    # 读取图片字节并转 base64
    try:
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        mime_map = {
            "image/jpeg": "image/jpeg",
            "image/jpg": "image/jpeg",
            "image/png": "image/png",
            "image/gif": "image/gif",
            "image/webp": "image/webp",
        }
        mime_type = mime_map.get(content_type, "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片读取失败：{e}")

    # 调用 Vision API 识别文字
    try:
        result = await ai_service.extract_answer_from_image(
            image_base64=image_base64,
            mime_type=mime_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片识别失败：{e}")

    return {
        "code": 200,
        "data": {
            "recognized_text": result.get("answer", ""),
            "confidence": result.get("confidence", "low"),
        },
    }


@router.post("/grade/file")
async def grade_file_homework(
    subject: str = Form(...),
    title: str = Form("我的作业"),
    grade_level: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文件作业进行 AI 批改（流式返回）
    
    支持格式：PDF、DOCX、JPG、PNG（图片通过 AI 视觉识别）
    """
    if subject not in SUBJECTS:
        raise HTTPException(status_code=400, detail=f"不支持的学科，请选择：{', '.join(SUBJECTS)}")

    content_type = file.content_type or ""

    # 扩展支持的图片类型
    if content_type not in SUPPORTED_FILE_TYPES and content_type not in {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
    }:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件类型，请上传 PDF、Word、JPG 或 PNG 文件"
        )

    # 保存文件
    try:
        file_info = await save_upload_file(file, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败：{e}")

    file_type = file_info["file_type"]
    file_path = file_info["file_path"]
    original_name = file_info["original_name"]

    # 提取文本内容
    extracted_text = ""
    is_image = file_type in ("jpg", "jpeg", "png", "gif", "webp")

    if not is_image:
        extracted_text = extract_text(file_path, file_type)

    # 确定内容类型标识
    content_type_label = "image" if is_image else file_type

    # 创建批改记录
    grading = HomeworkGrading(
        user_id=current_user.id,
        title=title or original_name,
        subject=subject,
        grade_level=grade_level or current_user.grade,
        content_type=content_type_label,
        content_text=extracted_text if extracted_text else None,
        file_path=file_path,
        file_name=original_name,
        status="processing",
    )
    db.add(grading)
    db.commit()
    db.refresh(grading)
    grading_id = grading.id

    # 准备批改内容
    grade_level_val = grade_level or current_user.grade or ""

    # 图片：读取文件字节并转为 base64，交给 Vision API
    image_base64: str = ""
    image_mime_type: str = content_type  # 保留原始 MIME 类型

    if is_image:
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            # 统一 MIME 类型映射
            mime_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "webp": "image/webp",
            }
            image_mime_type = mime_map.get(file_type, "image/jpeg")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图片读取失败：{e}")

    full_report = []

    async def generate():
        try:
            if is_image:
                # 图片：使用 Vision API 批改
                gen = ai_service.grade_homework_image(
                    subject=subject,
                    grade_level=grade_level_val,
                    image_base64=image_base64,
                    mime_type=image_mime_type,
                )
            else:
                # 文本/PDF/Word：使用普通文本批改
                grading_content = extracted_text or f"[文件 {original_name} 内容解析失败，请检查文件格式]"
                gen = ai_service.grade_homework(
                    subject=subject,
                    grade_level=grade_level_val,
                    content=grading_content,
                )

            async for chunk in gen:
                full_report.append(chunk)
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk}, ensure_ascii=False)}\n\n"

            report_text = "".join(full_report)
            score = await ai_service.extract_score_from_report(report_text)

            record = db.query(HomeworkGrading).filter(HomeworkGrading.id == grading_id).first()
            if record:
                record.status = "done"
                record.detailed_feedback = report_text
                record.score = score
                record.graded_at = datetime.utcnow()
                db.commit()

            yield f"data: {json.dumps({'type': 'done', 'grading_id': grading_id, 'score': score}, ensure_ascii=False)}\n\n"

        except Exception as e:
            record = db.query(HomeworkGrading).filter(HomeworkGrading.id == grading_id).first()
            if record:
                record.status = "error"
                db.commit()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history")
def get_grading_history(
    page: int = 1,
    size: int = 20,
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取作业批改历史记录"""
    query = db.query(HomeworkGrading).filter(
        HomeworkGrading.user_id == current_user.id
    )
    if subject:
        query = query.filter(HomeworkGrading.subject == subject)

    total = query.count()
    items = query.order_by(HomeworkGrading.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return {
        "code": 200,
        "data": {
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "subject": item.subject,
                    "grade_level": item.grade_level,
                    "content_type": item.content_type,
                    "file_name": item.file_name,
                    "status": item.status,
                    "score": item.score,
                    "created_at": item.created_at.isoformat(),
                    "graded_at": item.graded_at.isoformat() if item.graded_at else None,
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "size": size,
        },
    }


@router.get("/history/{grading_id}")
def get_grading_detail(
    grading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单条批改记录详情"""
    record = db.query(HomeworkGrading).filter(
        HomeworkGrading.id == grading_id,
        HomeworkGrading.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="批改记录不存在")

    return {
        "code": 200,
        "data": {
            "id": record.id,
            "title": record.title,
            "subject": record.subject,
            "grade_level": record.grade_level,
            "content_type": record.content_type,
            "content_text": record.content_text,
            "file_name": record.file_name,
            "status": record.status,
            "score": record.score,
            "detailed_feedback": record.detailed_feedback,
            "created_at": record.created_at.isoformat(),
            "graded_at": record.graded_at.isoformat() if record.graded_at else None,
        },
    }


@router.delete("/history/{grading_id}")
def delete_grading(
    grading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除批改记录"""
    record = db.query(HomeworkGrading).filter(
        HomeworkGrading.id == grading_id,
        HomeworkGrading.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="批改记录不存在")

    db.delete(record)
    db.commit()
    return {"code": 200, "message": "已删除"}
