import base64
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentOut, DocumentAnalyzeRequest
from app.services.document_service import save_upload_file, extract_text, ocr_pdf_pages_concurrent
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/documents", tags=["文档"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_info = await save_upload_file(file, current_user.id)
    doc_title = title or file_info["original_name"]

    doc = Document(
        user_id=current_user.id,
        title=doc_title,
        subject=subject,
        file_type=file_info["file_type"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 提取文本 - 使用内存中的字节内容，避免重复读取文件
    try:
        file_bytes = file_info.get("content")
        if file_info["file_type"] in ("jpg", "png"):
            # 图片文件：直接使用 Vision OCR（使用内存字节，不重新读文件）
            try:
                mime_type = "image/jpeg" if file_info["file_type"] == "jpg" else "image/png"
                image_base64 = base64.b64encode(file_bytes).decode("utf-8")
                result = await ai_service.ocr_image_for_reading(
                    image_base64=image_base64,
                    mime_type=mime_type,
                )
                text = result.get("text", "").strip()
                if not text:
                    text = "[图片内容为空或无法识别]"
            except Exception as _e:
                text = f"[图片OCR识别失败：{_e}]"
        else:
            text = extract_text(file_info["file_path"], file_info["file_type"])

            # ── 图片型 PDF 降级：文字层为空时，用 Vision OCR 逐页识别 ──────────────
            if file_info["file_type"] == "pdf" and (not text or text.startswith("[")):
                try:
                    text = await _ocr_pdf_pages(file_bytes)
                except Exception as _e:
                    text = f"[扫描版PDF，OCR识别失败：{_e}]"

        doc.content_text = text[:50000] if text else ""
        doc.status = "done"
        doc.processed_at = datetime.utcnow()
    except Exception as e:
        doc.status = "error"
    db.commit()

    return {"code": 200, "data": DocumentOut.model_validate(doc)}


@router.get("")
def list_documents(
    subject: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if subject:
        query = query.filter(Document.subject == subject)
    total = query.count()
    docs = query.order_by(Document.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {"code": 200, "data": {"items": [DocumentOut.model_validate(d) for d in docs], "total": total}}


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"code": 200, "data": DocumentOut.model_validate(doc)}


@router.post("/{doc_id}/analyze")
async def analyze_document(
    doc_id: int,
    data: DocumentAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not doc.content_text:
        raise HTTPException(status_code=400, detail="文档内容为空或尚未解析完成")

    full_response = []

    async def generate():
        async for chunk in ai_service.analyze_document(doc.content_text, data.task):
            full_response.append(chunk)
            yield f"data: {json.dumps({'type': 'content', 'delta': chunk}, ensure_ascii=False)}\n\n"

        full_content = "".join(full_response)
        if data.task == "summarize":
            doc.ai_summary = full_content
        elif data.task == "extract_key_points":
            doc.key_points = full_content
        db.commit()
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    import os
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"code": 200, "message": "删除成功"}


async def _ocr_pdf_pages(pdf_bytes: bytes) -> str:
    """将扫描版 PDF 每页并发调用 Vision OCR，拼接返回全文。

    使用 document_service 中的共享实现以避免代码重复。
    """
    return await ocr_pdf_pages_concurrent(pdf_bytes, ai_service)
