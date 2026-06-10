from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict


class PlanGenerateRequest(BaseModel):
    subjects: List[str]
    exam_date: date
    daily_hours: float
    weak_subjects: List[str] = []


class PlanTaskOut(BaseModel):
    id: int
    subject: str
    topic: str
    task_type: str
    duration_minutes: int
    is_done: bool
    order_num: int
    ai_content: Optional[str] = None
    submission_text: Optional[str] = None
    submission_image: Optional[str] = None
    evaluation: Optional[str] = None
    eval_score: Optional[float] = None
    completion_mode: Optional[str] = None
    # 练习题字段
    quiz_data: Optional[str] = None
    quiz_submission: Optional[str] = None
    quiz_evaluation: Optional[str] = None
    quiz_score: Optional[float] = None

    class Config:
        from_attributes = True


class PlanOut(BaseModel):
    plan_id: int
    start_date: date
    end_date: date
    total_days: int
    tasks_by_date: Dict[str, List[PlanTaskOut]]


class TaskDoneUpdate(BaseModel):
    is_done: bool


class PomodoroCreate(BaseModel):
    subject: Optional[str] = None
    duration_minutes: int = 25
    completed: bool = True


class TaskSubmitRequest(BaseModel):
    submission_text: Optional[str] = None
