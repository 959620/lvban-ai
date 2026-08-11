"""
Edu-Agent 启动入口。

职责（保持精简）：
1. 创建 FastAPI 应用
2. 挂载 API 路由
3. 生命周期内初始化 DB / 启停调度器
4. 提供前端静态页

运行：
  cd Edu-Agent
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  cp config/.env.example .env
  uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.database import init_db
from app.scheduler.jobs import shutdown_scheduler, start_scheduler
from config.settings import get_settings

settings = get_settings()
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期：启动时准备环境，关闭时清理调度器。"""
    init_db()
    if settings.scheduler_enabled:
        start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.app_name,
    description="AI 个人教务助手 Agent — 任务管理 / 提醒 / 学生跟进",
    version="0.7.0-ai-parse",
    lifespan=lifespan,
)

app.include_router(api_router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    """返回简易前端首页。"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Edu-Agent is running", "docs": "/docs"}
