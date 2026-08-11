"""
学生信息 API（占位）。

后续提供学生档案 CRUD，供任务关联与教务看板使用。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/students", tags=["students"])
