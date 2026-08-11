"""
API 路由汇总。

设计原因：main.py 只挂载一个总路由，具体资源拆到独立文件，便于按功能扩展。
"""

from fastapi import APIRouter

from app.api import health, tasks

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(tasks.router)

# Step 5+ 将在此挂载：
# from app.api import students, notifications
# api_router.include_router(students.router)
# api_router.include_router(notifications.router)
