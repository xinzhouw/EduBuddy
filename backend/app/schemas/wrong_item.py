from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


class WrongItemCreate(BaseModel):
    question: str
    correct_answer: str
    user_wrong_answer: Optional[str] = None
    subject: str
    tags: List[str] = []


class WrongItemOut(BaseModel):
    id: int
    question: str
    correct_answer: str
    user_wrong_answer: Optional[str] = None
    subject: str
    tags: str
    mastery: str
    review_count: int
    next_review_at: Optional[date] = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class MasteryUpdate(BaseModel):
    mastery: str  # 'unmastered'/'fuzzy'/'mastered'


class ReviewSubmit(BaseModel):
    answer: str
    is_correct: bool


class ReviewResult(BaseModel):
    next_review_at: Optional[date]
    review_count: int
    mastery: str
    message: str
