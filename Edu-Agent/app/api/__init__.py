"""
API 路由汇总。

设计原因：main.py 只挂载一个总路由，具体资源拆到独立文件，便于按功能扩展。
"""

from fastapi import APIRouter

from app.api import health, notifications, tasks

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(notifications.router)

# 后续：
# from app.api import students
# api_router.include_router(students.router)
