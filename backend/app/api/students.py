from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.constants import APPLICATION_STAGES, MAJORS, SCHOOL_PRIORITIES
from app.core.security import get_current_user
from app.database import get_db
from app.models import Tag, User
from app.schemas import StudentCreate, StudentListOut, StudentOptionsOut, StudentOut, StudentUpdate, TagOut
from app.services import students as student_service

router = APIRouter(prefix="/students", tags=["学生"])


@router.get("/options", response_model=StudentOptionsOut, summary="学生表单选项")
def student_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentOptionsOut:
    """获取专业、申请阶段、标签等下拉选项。"""
    _ = current_user
    tags = db.query(Tag).order_by(Tag.id.asc()).all()
    return StudentOptionsOut(
        majors=MAJORS,
        application_stages=APPLICATION_STAGES,
        school_priorities=SCHOOL_PRIORITIES,
        tags=[TagOut.model_validate(tag) for tag in tags],
    )


@router.get("", response_model=StudentListOut, summary="学生列表")
def list_students(
    q: str | None = Query(default=None, title="搜索关键词", description="姓名 / 专业 / 国家 / 目标专业"),
    major: str | None = Query(default=None, title="专业方向"),
    application_stage: str | None = Query(default=None, title="申请阶段"),
    tag_id: int | None = Query(default=None, title="标签 ID"),
    intake_year: int | None = Query(default=None, title="入学年份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentListOut:
    """按当前登录老师筛选名下学生。"""
    items = student_service.list_owned_students(
        db,
        current_user.id,
        q=q,
        major=major,
        application_stage=application_stage,
        tag_id=tag_id,
        intake_year=intake_year,
    )
    return StudentListOut(items=[StudentOut.model_validate(item) for item in items], total=len(items))


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED, summary="新建学生")
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentOut:
    """创建学生档案，支持多目标院校与标签。"""
    try:
        student = student_service.create_student(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StudentOut.model_validate(student)


@router.get("/{student_id}", response_model=StudentOut, summary="学生详情")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentOut:
    student = student_service.get_owned_student(db, student_id, current_user.id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return StudentOut.model_validate(student)


@router.put("/{student_id}", response_model=StudentOut, summary="更新学生")
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentOut:
    student = student_service.get_owned_student(db, student_id, current_user.id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    try:
        updated = student_service.update_student(db, student, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StudentOut.model_validate(updated)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除学生")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    student = student_service.get_owned_student(db, student_id, current_user.id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    student_service.delete_student(db, student)
