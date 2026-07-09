import base64
import json
import os
import re
import uuid
from datetime import date, datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.study_plan import StudyPlan, PlanTask, Pomodoro
from app.schemas.plan import PlanGenerateRequest, PlanTaskOut, PlanOut, TaskDoneUpdate, PomodoroCreate
from app.services.ai_service import ai_service
from app.config import get_settings

router = APIRouter(prefix="/api/plan", tags=["学习计划"])
settings = get_settings()


@router.post("/generate")
async def generate_plan(
    data: PlanGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """制定学习计划：只生成每天学习任务的索引（日期/学科/主题/类型/时长），不生成内容本身"""
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
    # 先 commit 保存 plan，释放 SQLite 写锁，避免 AI 长时间调用期间 "database is locked"
    db.commit()

    user_language = current_user.language or "zh"

    # 生成任务索引（只包含 date/subject/topic/task_type/duration_minutes，不含内容）
    tasks_data = await ai_service.generate_study_plan(
        subjects=data.subjects,
        exam_date=str(exam_date),
        daily_hours=data.daily_hours,
        weak_subjects=data.weak_subjects,
        start_date=str(start_date),
        language=user_language,
    )

    import logging
    logger = logging.getLogger("plan_generate")

    tasks_by_date = {}
    for i, t in enumerate(tasks_data):
        task_date_str = t.get("date", str(start_date))
        try:
            task_date = date.fromisoformat(task_date_str)
        except ValueError as e:
            logger.warning(f"日期解析失败: {task_date_str!r} -> {e}")
            continue
        if task_date < start_date or task_date > exam_date:
            logger.debug(f"过滤掉超出范围的任务: date={task_date}, start={start_date}, exam={exam_date}")
            continue

        try:
            task = PlanTask(
                plan_id=plan.id,
                user_id=current_user.id,
                date=task_date,
                subject=t.get("subject", ""),
                topic=t.get("topic", ""),
                task_type=t.get("task_type", "study"),
                duration_minutes=t.get("duration_minutes", 60),
                order_num=i + 1,
                # 不生成 ai_content，留空，等当天第一次登录时触发生成
            )
            db.add(task)
            db.flush()

            date_key = str(task_date)
            if date_key not in tasks_by_date:
                tasks_by_date[date_key] = []
            tasks_by_date[date_key].append(PlanTaskOut.model_validate(task))
        except Exception as e:
            logger.error(f"写入任务失败: {t} -> {e}", exc_info=True)
            db.rollback()
            raise HTTPException(status_code=500, detail=f"写入任务时发生错误: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        logger.error(f"commit 失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存计划时发生错误: {str(e)}")

    logger.info(f"计划生成完成: plan_id={plan.id}, 学科={data.subjects}, 任务数={sum(len(v) for v in tasks_by_date.values())}")

    # 若生成任务数为0，给出友好提示
    if not tasks_by_date:
        db.query(StudyPlan).filter(StudyPlan.id == plan.id).update({"is_active": False})
        db.commit()
        raise HTTPException(
            status_code=422,
            detail="AI 未能生成有效任务，请检查：①考试日期是否至少在1周后；②备考学科是否已选择"
        )

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
        return {"code": 200, "data": [], "needs_generate": False}

    today = date.today()
    tasks = db.query(PlanTask).filter(
        PlanTask.plan_id == plan.id, PlanTask.date == today
    ).order_by(PlanTask.order_num).all()

    # 判断今日任务是否需要生成内容（所有任务都没有 ai_content）
    needs_generate = len(tasks) > 0 and all(not t.ai_content for t in tasks)

    return {
        "code": 200,
        "data": [PlanTaskOut.model_validate(t) for t in tasks],
        "needs_generate": needs_generate,
    }


@router.post("/today/generate-content")
async def generate_today_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    为当日所有任务批量生成 AI 学习内容（SSE 流式）。
    每个任务逐一生成，生成完成后保存到数据库。
    用于用户每天第一次登录时（如果当日在计划时间范围内）触发。
    """
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == current_user.id, StudyPlan.is_active == True
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="暂无学习计划")

    today = date.today()
    # 检查今天是否在计划时间范围内
    if today < plan.start_date or today > plan.exam_date:
        raise HTTPException(status_code=400, detail="今日不在学习计划时间范围内")

    tasks = db.query(PlanTask).filter(
        PlanTask.plan_id == plan.id, PlanTask.date == today
    ).order_by(PlanTask.order_num).all()

    if not tasks:
        raise HTTPException(status_code=404, detail="今日暂无学习任务")

    # 只生成尚未有内容的任务
    tasks_to_generate = [t for t in tasks if not t.ai_content]
    if not tasks_to_generate:
        # 所有任务都已有内容，直接返回
        async def already_done():
            yield f"data: {json.dumps({'done': True, 'message': '今日学习内容已准备好'}, ensure_ascii=False)}\n\n"
        return StreamingResponse(already_done(), media_type="text/event-stream")

    grade = getattr(current_user, "grade", "高中") or "高中"
    user_language = current_user.language or "zh"

    # 收集任务信息（在 StreamingResponse 的 generator 外部，避免 session 问题）
    task_infos = [
        {
            "id": t.id,
            "subject": t.subject,
            "topic": t.topic,
            "task_type": t.task_type,
            "duration_minutes": t.duration_minutes,
        }
        for t in tasks_to_generate
    ]

    async def generate():
        total = len(task_infos)
        for idx, task_info in enumerate(task_infos):
            task_id = task_info["id"]
            # 发送进度通知
            yield f"data: {json.dumps({'progress': {'current': idx + 1, 'total': total, 'task_id': task_id, 'subject': task_info['subject'], 'topic': task_info['topic']}}, ensure_ascii=False)}\n\n"

            full_content = []
            try:
                async for delta in ai_service.generate_task_content(
                    subject=task_info["subject"],
                    topic=task_info["topic"],
                    task_type=task_info["task_type"],
                    duration_minutes=task_info["duration_minutes"],
                    grade=grade,
                    language=user_language,
                ):
                    full_content.append(delta)
                    yield f"data: {json.dumps({'task_id': task_id, 'delta': delta}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'task_id': task_id, 'error': str(e)}, ensure_ascii=False)}\n\n"
                continue

            # 保存到数据库
            content_str = "".join(full_content)
            try:
                from app.database import SessionLocal
                save_db = SessionLocal()
                try:
                    db_task = save_db.query(PlanTask).filter(PlanTask.id == task_id).first()
                    if db_task:
                        db_task.ai_content = content_str
                        save_db.commit()
                finally:
                    save_db.close()
            except Exception:
                pass

            yield f"data: {json.dumps({'task_id': task_id, 'task_done': True}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'done': True, 'total': total}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


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
    # 只有当日任务可以修改完成状态
    today = date.today()
    if task.date != today:
        raise HTTPException(status_code=403, detail="只能修改当日任务的完成状态，历史任务已归档")
    task.is_done = data.is_done
    task.done_at = datetime.utcnow() if data.is_done else None
    if data.is_done and not task.completion_mode:
        task.completion_mode = "manual"
    elif not data.is_done:
        task.completion_mode = None
    db.commit()
    return {"code": 200, "message": "已更新"}


@router.post("/tasks/{task_id}/generate-content")
async def generate_task_content(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 生成任务学习内容（SSE 流式），生成完成后保存到数据库。只允许当日任务操作。"""
    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 只有当日任务可以重新生成内容
    today = date.today()
    if task.date != today:
        raise HTTPException(status_code=403, detail="只有当日任务可以生成内容，历史任务已归档只读")

    grade = getattr(current_user, "grade", "高中") or "高中"
    user_language = current_user.language or "zh"
    subject = task.subject
    topic = task.topic
    task_type = task.task_type
    duration_minutes = task.duration_minutes

    async def generate():
        full_content = []
        try:
            async for delta in ai_service.generate_task_content(
                subject=subject,
                topic=topic,
                task_type=task_type,
                duration_minutes=duration_minutes,
                grade=grade,
                language=user_language,
            ):
                full_content.append(delta)
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        # 保存生成的内容到数据库
        content_str = "".join(full_content)
        try:
            db_task = db.query(PlanTask).filter(PlanTask.id == task_id).first()
            if db_task:
                db_task.ai_content = content_str
                db.commit()
        except Exception:
            pass

        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/tasks/{task_id}/submit")
async def submit_task(
    task_id: int,
    submission_text: str = Form(default=""),
    file: UploadFile = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交学习成果并由 AI 评判（SSE 流式），评判完成后保存结果并自动标记任务完成。只允许当日任务操作。"""
    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 只有当日任务可以提交
    today = date.today()
    if task.date != today:
        raise HTTPException(status_code=403, detail="只有当日任务可以提交，历史任务已归档只读")

    if not submission_text and not file:
        raise HTTPException(status_code=400, detail="请提供文字说明或上传图片")

    subject = task.subject
    topic = task.topic
    task_type = task.task_type
    user_language = current_user.language or "zh"

    # 处理图片上传
    image_base64 = ""
    mime_type = "image/jpeg"
    saved_image_path = ""

    if file and file.content_type and file.content_type.startswith("image/"):
        file_bytes = await file.read()
        image_base64 = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = file.content_type

        # 保存图片到上传目录
        ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
        filename = f"plan_submission_{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(settings.upload_dir, filename)
        os.makedirs(settings.upload_dir, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        saved_image_path = f"/uploads/{filename}"

    # 先保存提交内容
    task.submission_text = submission_text or None
    task.submission_image = saved_image_path or None
    db.commit()

    async def evaluate():
        full_eval = []
        try:
            async for delta in ai_service.evaluate_submission(
                subject=subject,
                topic=topic,
                task_type=task_type,
                submission_text=submission_text,
                image_base64=image_base64,
                mime_type=mime_type,
                language=user_language,
            ):
                full_eval.append(delta)
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        eval_str = "".join(full_eval)

        # 提取分数
        score = await ai_service.extract_score_from_report(eval_str)

        # 保存评判结果，分数 >= 60 自动标记任务完成
        try:
            db_task = db.query(PlanTask).filter(PlanTask.id == task_id).first()
            if db_task:
                db_task.evaluation = eval_str
                db_task.eval_score = score
                db_task.completion_mode = "submission"
                if score >= 60:
                    db_task.is_done = True
                    db_task.done_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass

        yield f"data: {json.dumps({'done': True, 'score': score, 'passed': score >= 60}, ensure_ascii=False)}\n\n"

    return StreamingResponse(evaluate(), media_type="text/event-stream")


@router.post("/tasks/{task_id}/generate-quiz")
async def generate_task_quiz(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 生成任务练习题（SSE 流式），生成完成后保存到数据库。只允许当日任务操作。"""
    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 只有当日任务可以生成练习题
    today = date.today()
    if task.date != today:
        raise HTTPException(status_code=403, detail="只有当日任务可以生成练习题，历史任务已归档只读")

    grade = getattr(current_user, "grade", "高中") or "高中"
    user_language = current_user.language or "zh"
    subject = task.subject
    topic = task.topic
    task_type = task.task_type

    async def generate():
        full_content = []
        try:
            async for delta in ai_service.generate_task_quiz(
                subject=subject,
                topic=topic,
                task_type=task_type,
                grade=grade,
                count=5,
                language=user_language,
            ):
                full_content.append(delta)
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        # 保存生成的练习题到数据库
        content_str = "".join(full_content)
        try:
            db_task = db.query(PlanTask).filter(PlanTask.id == task_id).first()
            if db_task:
                db_task.quiz_data = content_str
                db_task.quiz_submission = None
                db_task.quiz_evaluation = None
                db_task.quiz_score = None
                db.commit()
        except Exception:
            pass

        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/tasks/{task_id}/submit-quiz")
async def submit_task_quiz(
    task_id: int,
    answers: str = Form(...),  # JSON string: {"1": "A", "2": "答案", ...}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交练习题答案并由 AI 评判（SSE 流式），评判完成后保存结果。只允许当日任务操作。"""
    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 只有当日任务可以提交练习题
    today = date.today()
    if task.date != today:
        raise HTTPException(status_code=403, detail="只有当日任务可以提交练习题，历史任务已归档只读")

    if not task.quiz_data:
        raise HTTPException(status_code=400, detail="请先生成练习题")

    # 解析练习题和答案
    try:
        questions = json.loads(task.quiz_data)
        student_answers = json.loads(answers)
    except Exception:
        raise HTTPException(status_code=400, detail="数据格式错误")

    subject = task.subject
    topic = task.topic
    user_language = current_user.language or "zh"

    # ── 后端程序化计算客观题得分，并告知 AI 每题满分以便其评判简答题 ──
    import logging as _logging
    _log = _logging.getLogger("submit_quiz")
    total_q = len(questions) if questions else 1
    per_score = 100.0 / total_q
    _log.warning(f"[submit-quiz] task_id={task_id} total_q={total_q} per_score={per_score} student_answers={student_answers}")

    # 程序化批改客观题，记录简答题id
    short_ids = []      # 简答题 id（str），需要 AI 给分
    obj_scores: dict[str, float] = {}  # 客观题程序化得分 {qid: score}

    for q in questions:
        qid = str(q.get("id", ""))
        qtype = q.get("type", "")
        correct = str(q.get("answer", "")).strip()
        student = str(student_answers.get(qid, "")).strip()
        _log.warning(f"[submit-quiz] qid={qid} qtype={qtype} correct={correct!r} student={student!r}")

        if qtype in ("choice", "fill"):
            got = per_score if student.upper() == correct.upper() else 0.0
            obj_scores[qid] = got
            _log.warning(f"[submit-quiz] qid={qid} obj got={got}")
        else:
            short_ids.append(qid)
            _log.warning(f"[submit-quiz] qid={qid} is short/subjective")

    auto_score = sum(obj_scores.values())
    _log.warning(f"[submit-quiz] auto_score={auto_score} short_ids={short_ids}")

    # 保存提交的答案
    task.quiz_submission = answers
    db.commit()

    async def evaluate():
        full_eval = []
        try:
            async for delta in ai_service.evaluate_task_quiz(
                subject=subject,
                topic=topic,
                questions=questions,
                student_answers=student_answers,
                per_score=per_score,
                obj_scores=obj_scores,
                language=user_language,
            ):
                full_eval.append(delta)
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        eval_str = "".join(full_eval)

        # 计算最终分数：客观题用程序化得分 + 简答题从 AI 表格逐题提取
        if not short_ids:
            # 全部客观题：直接用程序化得分
            score = round(auto_score)
        else:
            # 从 AI 报告的逐题表格中提取各简答题得分
            # 表格格式：| 题号 | 题型 | 得分 | 满分 | 评价 |
            # 例：| 3 | 简答题 | 12 | 20 | ...
            short_score = 0.0
            for qid in short_ids:
                # 匹配表格中该题的得分列（第3列）
                pattern = rf'\|\s*{re.escape(qid)}\s*\|[^|]+\|\s*(\d+(?:\.\d+)?)\s*\|'
                m = re.search(pattern, eval_str)
                if m:
                    short_score += float(m.group(1))
                    _log.warning(f"[submit-quiz] qid={qid} short AI got={m.group(1)}")
                else:
                    # 找不到时给 50% 估算
                    short_score += per_score * 0.5
                    _log.warning(f"[submit-quiz] qid={qid} short fallback 50%")
            score = round(auto_score + short_score)

        score = max(0, min(100, score))

        # 保存评判结果，分数 >= 60 自动标记任务完成
        try:
            db_task = db.query(PlanTask).filter(PlanTask.id == task_id).first()
            if db_task:
                db_task.quiz_evaluation = eval_str
                db_task.quiz_score = score
                if score >= 60:
                    db_task.is_done = True
                    db_task.done_at = datetime.utcnow()
                    db_task.completion_mode = "quiz"
                db.commit()
        except Exception:
            pass

        yield f"data: {json.dumps({'done': True, 'score': score, 'passed': score >= 60}, ensure_ascii=False)}\n\n"

    return StreamingResponse(evaluate(), media_type="text/event-stream")


@router.get("/tasks/{task_id}")
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个任务详情（含 AI 内容和评判结果）"""
    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"code": 200, "data": PlanTaskOut.model_validate(task)}


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
