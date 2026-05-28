import json
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
from app.services.document_service import save_upload_file, extract_text
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

    # 异步提取文本
    try:
        text = extract_text(file_info["file_path"], file_info["file_type"])
        doc.content_text = text[:50000]  # 限制大小
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
