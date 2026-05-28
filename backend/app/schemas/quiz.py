from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class QuizGenerateRequest(BaseModel):
    subject: str
    topic: str
    difficulty: int  # 1-4
    question_types: List[str]
    count: int = 5


class QuestionOut(BaseModel):
    id: int
    type: str
    content: str
    options: Optional[str] = None
    difficulty: int

    class Config:
        from_attributes = True


class AnswerItem(BaseModel):
    question_id: int
    answer: str
    time_spent: int = 0


class QuizSubmitRequest(BaseModel):
    answers: List[AnswerItem]


class AnswerResult(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: str
    user_answer: str
    explanation: Optional[str] = None


class QuizResult(BaseModel):
    total: int
    correct: int
    accuracy: float
    time_spent: int
    results: List[AnswerResult]
    wrong_items_added: List[int] = []


class QuizSessionOut(BaseModel):
    id: str
    subject: str
    topic: str
    total: int
    correct: int
    accuracy: float
    created_at: datetime

    class Config:
        from_attributes = True
