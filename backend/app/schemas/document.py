from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DocumentOut(BaseModel):
    id: int
    title: str
    subject: Optional[str] = None
    file_type: str
    file_size: int
    status: str
    content_text: Optional[str] = None
    key_points: Optional[str] = None
    ai_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentAnalyzeRequest(BaseModel):
    task: str  # 'extract_key_points'/'summarize'/'generate_quiz'


class StudyLogCreate(BaseModel):
    subject: Optional[str] = None
    duration_minutes: int
    activity_type: str
