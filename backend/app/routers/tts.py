"""
读书郎 TTS 模块 — 文字提取接口
支持：图片（Vision OCR）、PDF、DOCX、纯文本
"""
import base64
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.document_service import extract_text

router = APIRouter(prefix="/api/tts", tags=["读书郎TTS"])

# 支持的文件类型
SUPPORTED_MIME = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}

IMAGE_MIMES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class ExtractTextRequest(BaseModel):
    text: str


@router.post("/extract-text/plain")
async def extract_text_from_plain(
    data: ExtractTextRequest,
    current_user: User = Depends(get_current_user),
):
    """直接提交纯文本，返回清理后的文本（用于朗读前预处理）"""
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    if len(text) > 50000:
        raise HTTPException(status_code=400, detail="文本过长，请控制在 50000 字以内")

    # 简单清理：去除多余空行
    cleaned = re.sub(r'\n{3,}', '\n\n', text).strip()
    return {
        "code": 200,
        "data": {
            "text": cleaned,
            "char_count": len(cleaned),
            "source": "plain",
        },
    }


@router.post("/extract-text/file")
async def extract_text_from_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """从上传文件（图片/PDF/DOCX）提取文本内容"""
    content_type = (file.content_type or "").lower()

    if content_type not in SUPPORTED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 '{content_type}'，请上传 PDF、Word、JPG、PNG、GIF 或 WebP 文件",
        )

    # 读取文件内容
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，请控制在 20MB 以内")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")

    file_type = SUPPORTED_MIME[content_type]
    is_image = content_type in IMAGE_MIMES

    # ── 图片：使用 Vision OCR ──────────────────────────────────────────────────
    if is_image:
        image_base64 = base64.b64encode(file_bytes).decode("utf-8")
        # 统一 MIME 类型
        mime_map = {
            "image/jpg": "image/jpeg",
            "image/jpeg": "image/jpeg",
            "image/png": "image/png",
            "image/gif": "image/gif",
            "image/webp": "image/webp",
        }
        mime_type = mime_map.get(content_type, "image/jpeg")

        try:
            result = await ai_service.ocr_image_for_reading(
                image_base64=image_base64,
                mime_type=mime_type,
            )
            extracted = result.get("text", "").strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图片文字识别失败：{e}")

        if not extracted:
            raise HTTPException(status_code=422, detail="图片中未识别到可朗读的文字内容")

        return {
            "code": 200,
            "data": {
                "text": extracted,
                "char_count": len(extracted),
                "source": "image_ocr",
                "file_name": file.filename or "image",
            },
        }

    # ── PDF / DOCX：直接提取文本 ───────────────────────────────────────────────
    import tempfile, os

    suffix = f".{file_type}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        extracted = extract_text(tmp_path, file_type)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if not extracted or extracted.startswith("["):
        raise HTTPException(
            status_code=422,
            detail=f"文件文字提取失败：{extracted or '内容为空'}",
        )

    # 清理多余空行
    cleaned = re.sub(r'\n{3,}', '\n\n', extracted).strip()

    return {
        "code": 200,
        "data": {
            "text": cleaned,
            "char_count": len(cleaned),
            "source": file_type,
            "file_name": file.filename or f"file.{file_type}",
        },
    }
