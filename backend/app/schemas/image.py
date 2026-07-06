from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ImageUploadRequest(BaseModel):
    """图片上传请求（multipart/form-data）"""
    session_id: Optional[str] = None
    question: str
    subject: str = "数学"
    # images: List[UploadFile]  # FastAPI 自动处理


class ImageResponse(BaseModel):
    """图片信息响应"""
    id: str
    file_path: str
    original_filename: str
    file_size: int
    file_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatImageModel(BaseModel):
    """聊天消息中的图片信息"""
    image_ids: Optional[List[str]] = None
    ocr_text: Optional[str] = None
    vision_description: Optional[str] = None
