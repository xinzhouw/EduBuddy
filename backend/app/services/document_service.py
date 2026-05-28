import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import get_settings

settings = get_settings()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "jpg",
    "image/png": "png",
}


async def save_upload_file(file: UploadFile, user_id: int) -> dict:
    """保存上传文件，返回文件信息"""
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持 PDF、DOCX、JPG、PNG")

    file_ext = ALLOWED_TYPES[content_type]

    # 检查文件大小
    content = await file.read()
    max_size = settings.max_file_size_bytes
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {settings.max_file_size_mb}MB）")

    # 保存文件
    upload_dir = Path(settings.upload_dir) / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}.{file_ext}"
    file_path = upload_dir / file_name
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "file_path": str(file_path),
        "file_type": file_ext,
        "file_size": len(content),
        "original_name": file.filename or "unknown",
    }


def extract_text(file_path: str, file_type: str) -> str:
    """从文件中提取文本内容"""
    try:
        if file_type == "pdf":
            return _extract_pdf(file_path)
        elif file_type == "docx":
            return _extract_docx(file_path)
        elif file_type in ("jpg", "png"):
            return _extract_image(file_path)
    except Exception as e:
        return f"[文件解析失败: {e}]"
    return ""


def _extract_pdf(file_path: str) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except ImportError:
        return "[PDF解析需要 PyMuPDF，请安装：pip install PyMuPDF]"


def _extract_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()
    except ImportError:
        return "[DOCX解析需要 python-docx，请安装：pip install python-docx]"


def _extract_image(file_path: str) -> str:
    """图片OCR（使用OpenAI Vision API）"""
    return "[图片OCR功能需要 OpenAI Vision API，请在上传后通过 AI 分析获取内容]"
