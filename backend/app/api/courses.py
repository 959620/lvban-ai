from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.constants import COURSE_SUITABLE_STAGES, COURSE_TYPES, MAJORS
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.course import CourseCreate, CourseListOut, CourseOptionsOut, CourseOut, CourseUpdate
from app.services import courses as course_service

router = APIRouter(prefix="/courses", tags=["课程库"])


@router.get("/options", response_model=CourseOptionsOut, summary="课程表单选项")
def course_options(current_user: User = Depends(get_current_user)) -> CourseOptionsOut:
    _ = current_user
    return CourseOptionsOut(
        course_types=COURSE_TYPES,
        majors=MAJORS,
        suitable_stages=COURSE_SUITABLE_STAGES,
    )


@router.get("", response_model=CourseListOut, summary="课程列表")
def list_courses(
    q: str | None = Query(default=None, title="搜索关键词"),
    course_type: str | None = Query(default=None, title="课程类型"),
    major: str | None = Query(default=None, title="适合专业"),
    stage: str | None = Query(default=None, title="适合阶段"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseListOut:
    items = course_service.list_courses(
        db,
        current_user.id,
        q=q,
        course_type=course_type,
        major=major,
        stage=stage,
    )
    return CourseListOut(items=[CourseOut.model_validate(item) for item in items], total=len(items))


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED, summary="新建课程")
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseOut:
    course = course_service.create_course(db, current_user.id, payload)
    return CourseOut.model_validate(course)


@router.get("/{course_id}", response_model=CourseOut, summary="课程详情")
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseOut:
    course = course_service.get_owned_course(db, course_id, current_user.id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return CourseOut.model_validate(course)


@router.put("/{course_id}", response_model=CourseOut, summary="更新课程")
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseOut:
    course = course_service.get_owned_course(db, course_id, current_user.id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    updated = course_service.update_course(db, course, payload)
    return CourseOut.model_validate(updated)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除课程")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    course = course_service.get_owned_course(db, course_id, current_user.id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    course_service.delete_course(db, course)
