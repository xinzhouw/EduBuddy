import json
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.study_plan import StudyPlan, PlanTask, Pomodoro
from app.schemas.plan import PlanGenerateRequest, PlanTaskOut, PlanOut, TaskDoneUpdate, PomodoroCreate
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/plan", tags=["学习计划"])


@router.post("/generate")
async def generate_plan(
    data: PlanGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_date = date.today()
    exam_date = data.exam_date

    # 停用旧计划
    db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id, StudyPlan.is_active == True).update({"is_active": False})

    # 创建新计划
    plan = StudyPlan(
        user_id=current_user.id,
        subjects=json.dumps(data.subjects, ensure_ascii=False),
        exam_date=exam_date,
        daily_hours=data.daily_hours,
        weak_subjects=json.dumps(data.weak_subjects, ensure_ascii=False),
        start_date=start_date,
    )
    db.add(plan)
    db.flush()

    # 生成任务
    tasks_data = await ai_service.generate_study_plan(
        subjects=data.subjects,
        exam_date=str(exam_date),
        daily_hours=data.daily_hours,
        weak_subjects=data.weak_subjects,
        start_date=str(start_date),
    )

    tasks_by_date = {}
    for i, t in enumerate(tasks_data):
        task_date_str = t.get("date", str(start_date))
        try:
            task_date = date.fromisoformat(task_date_str)
        except ValueError:
            continue
        if task_date < start_date or task_date > exam_date:
            continue

        task = PlanTask(
            plan_id=plan.id,
            user_id=current_user.id,
            date=task_date,
            subject=t.get("subject", ""),
            topic=t.get("topic", ""),
            task_type=t.get("task_type", "study"),
            duration_minutes=t.get("duration_minutes", 60),
            order_num=i + 1,
        )
        db.add(task)
        db.flush()

        date_key = str(task_date)
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(PlanTaskOut.model_validate(task))

    db.commit()

    total_days = (exam_date - start_date).days + 1
    return {"code": 200, "data": PlanOut(
        plan_id=plan.id,
        start_date=start_date,
        end_date=exam_date,
        total_days=total_days,
        tasks_by_date=tasks_by_date,
    )}


@router.get("/current")
def get_current_plan(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == current_user.id, StudyPlan.is_active == True
    ).first()
    if not plan:
        return {"code": 200, "data": None}

    tasks = db.query(PlanTask).filter(PlanTask.plan_id == plan.id).order_by(PlanTask.date, PlanTask.order_num).all()
    tasks_by_date = {}
    for task in tasks:
        date_key = str(task.date)
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(PlanTaskOut.model_validate(task))

    total_days = (plan.exam_date - plan.start_date).days + 1
    return {"code": 200, "data": PlanOut(
        plan_id=plan.id,
        start_date=plan.start_date,
        end_date=plan.exam_date,
        total_days=total_days,
        tasks_by_date=tasks_by_date,
    )}


@router.get("/today")
def get_today_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == current_user.id, StudyPlan.is_active == True
    ).first()
    if not plan:
        return {"code": 200, "data": []}

    today = date.today()
    tasks = db.query(PlanTask).filter(
        PlanTask.plan_id == plan.id, PlanTask.date == today
    ).order_by(PlanTask.order_num).all()

    return {"code": 200, "data": [PlanTaskOut.model_validate(t) for t in tasks]}


@router.put("/tasks/{task_id}/done")
def mark_task_done(
    task_id: int,
    data: TaskDoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.is_done = data.is_done
    task.done_at = datetime.utcnow() if data.is_done else None
    db.commit()
    return {"code": 200, "message": "已更新"}


@router.post("/pomodoro")
def record_pomodoro(
    data: PomodoroCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pomo = Pomodoro(
        user_id=current_user.id,
        subject=data.subject,
        duration_minutes=data.duration_minutes,
        completed=data.completed,
    )
    db.add(pomo)
    db.commit()
    return {"code": 200, "message": "番茄钟记录成功"}
