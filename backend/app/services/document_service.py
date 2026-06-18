import os
import uuid
import base64
import asyncio
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
    """保存上传文件，返回文件信息及内存中的字节内容"""
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
        "content": content,  # 返回内存中的字节，避免后续重复读取
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


async def ocr_pdf_pages_concurrent(pdf_bytes: bytes, ai_service) -> str:
    """并发 OCR 处理扫描版 PDF - 统一实现，避免代码重复

    使用 asyncio.gather 并发处理多页，相比顺序处理可提升 5-10 倍速度。
    依赖：PyMuPDF（fitz），容器中已安装。
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = doc.page_count

    # 预处理：将所有页面渲染成图片的 base64
    page_images = []
    for page_index in range(page_count):
        page = doc[page_index]
        # 渲染为 150 DPI 的 PNG（提高 OCR 精度）
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img_bytes = pix.tobytes("png")
        image_base64 = base64.b64encode(img_bytes).decode("utf-8")
        page_images.append((page_index, image_base64))

    doc.close()

    # 并发 OCR：使用 asyncio.gather 同时处理所有页面
    async def ocr_page(page_index: int, image_base64: str) -> tuple[int, str]:
        try:
            result = await ai_service.ocr_image_for_reading(
                image_base64=image_base64,
                mime_type="image/png",
            )
            page_text = result.get("text", "").strip()
        except Exception as e:
            page_text = f"[第 {page_index + 1} 页识别失败：{e}]"
        return page_index, page_text

    # 并发执行所有页面的 OCR
    tasks = [ocr_page(idx, img_b64) for idx, img_b64 in page_images]
    results = await asyncio.gather(*tasks)

    # 按原始顺序重新组织结果
    results.sort(key=lambda x: x[0])
    all_texts = [text for _, text in results if text]

    return "\n\n".join(all_texts)
