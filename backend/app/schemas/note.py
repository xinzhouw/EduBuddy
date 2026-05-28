from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class NoteCreate(BaseModel):
    title: str
    subject: str
    content: str = ""


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None


class NoteOut(BaseModel):
    id: int
    title: str
    subject: str
    content: str
    ai_summary: Optional[str] = None
    key_points: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FlashcardCreate(BaseModel):
    front: str
    back: str
    subject: str
    tags: List[str] = []


class FlashcardOut(BaseModel):
    id: int
    front: str
    back: str
    subject: str
    tags: str
    note_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
