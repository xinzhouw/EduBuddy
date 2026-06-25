from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import get_settings
from app.database import init_db
from app.routers import auth, ai, notes, quiz, wrong_book, plan, documents, stats, system, admin
from app.routers.notes import flashcard_router
from app.routers import homework
from app.routers import tts
from app.routers import advice, relations, monitor
from app.middleware.audit_middleware import AuditMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化数据库、确保上传目录存在、启动定时任务
    init_db()
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 启动定时任务
    from app.tasks.scheduler import start_scheduler
    scheduler = start_scheduler()

    yield

    # 关闭时：停止定时任务
    if scheduler:
        from app.tasks.scheduler import stop_scheduler
        stop_scheduler(scheduler)


app = FastAPI(
    title="EduBuddy API",
    description="AI 驱动的中学生个性化学习助手",
    version="1.0.0",
    lifespan=lifespan,
)


# 添加审计中间件（在 CORS 之前，以便捕获所有请求）
app.add_middleware(AuditMiddleware)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(notes.router)
app.include_router(flashcard_router)
app.include_router(quiz.router)
app.include_router(wrong_book.router)
app.include_router(plan.router)
app.include_router(documents.router)
app.include_router(stats.router)
app.include_router(homework.router)
app.include_router(tts.router)
app.include_router(advice.router)
app.include_router(relations.router)
app.include_router(monitor.router)
app.include_router(admin.router)

# 挂载静态文件（上传文件）
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/")
def root():
    return {"message": "EduBuddy API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
