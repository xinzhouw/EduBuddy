from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import get_settings
from app.database import init_db
from app.routers import auth, ai, notes, quiz, wrong_book, plan, documents, stats
from app.routers.notes import flashcard_router

settings = get_settings()

app = FastAPI(
    title="EduBuddy API",
    description="AI 驱动的中学生个性化学习助手",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(notes.router)
app.include_router(flashcard_router)
app.include_router(quiz.router)
app.include_router(wrong_book.router)
app.include_router(plan.router)
app.include_router(documents.router)
app.include_router(stats.router)

# 挂载静态文件（上传文件）
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.on_event("startup")
async def startup():
    init_db()
    os.makedirs(settings.upload_dir, exist_ok=True)


@app.get("/")
def root():
    return {"message": "EduBuddy API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
