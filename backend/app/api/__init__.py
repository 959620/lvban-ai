from fastapi import APIRouter

from app.api import ai, auth, courses, follow_ups, match, schedule, students, tasks, timeline

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(tasks.router)
api_router.include_router(courses.router)
api_router.include_router(schedule.router)
api_router.include_router(follow_ups.router)
api_router.include_router(match.router)
api_router.include_router(ai.router)
api_router.include_router(timeline.router)
