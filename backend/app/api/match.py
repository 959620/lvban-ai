from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.match import (
    CreateMatchTaskRequest,
    MatchCourseBrief,
    MatchResultOut,
    MatchRunOut,
    MatchRunRequest,
    MatchStudentBrief,
    ScriptBundleOut,
    ScriptRequest,
    parse_reasons,
)
from app.schemas.task import TaskCreate, TaskOut
from app.services import matching as matching_service
from app.services import scripts as script_service
from app.services import tasks as task_service

router = APIRouter(prefix="/match", tags=["课程匹配"])


def _serialize_run(run) -> MatchRunOut:
    results: list[MatchResultOut] = []
    for item in run.results:
        student = item.student
        results.append(
            MatchResultOut(
                id=item.id,
                student_id=item.student_id,
                student=MatchStudentBrief.model_validate(student) if student else None,
                score=item.score,
                rank=item.rank,
                reasons=parse_reasons(item.reasons),
                schools=[s.school_name for s in (student.schools or [])] if student else [],
                tags=[t.name for t in (student.tags or [])] if student else [],
            )
        )
    return MatchRunOut(
        id=run.id,
        course_id=run.course_id,
        course=MatchCourseBrief.model_validate(run.course) if run.course else None,
        engine_version=run.engine_version,
        created_at=run.created_at,
        results=results,
        total=len(results),
    )


@router.get("/status", summary="匹配引擎状态")
def match_status(current_user: User = Depends(get_current_user)) -> dict:
    _ = current_user
    return {
        "engine": "rule_v1",
        "scripts_engine": "template_v1",
        "ready": True,
        "message": "规则匹配与话术模板已就绪",
    }


@router.post("/run", response_model=MatchRunOut, summary="运行课程匹配")
def run_match(
    payload: MatchRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MatchRunOut:
    """按专业、阶段、作品集、标签、目标院校规则推荐学生。"""
    try:
        run = matching_service.run_course_match(
            db,
            owner_id=current_user.id,
            course_id=payload.course_id,
            min_score=payload.min_score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize_run(run)


@router.get("/runs/{run_id}", response_model=MatchRunOut, summary="匹配结果详情")
def get_match_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MatchRunOut:
    run = matching_service.get_match_run(db, run_id, current_user.id)
    if run is None:
        raise HTTPException(status_code=404, detail="匹配记录不存在")
    return _serialize_run(run)


@router.post("/scripts", response_model=ScriptBundleOut, summary="生成销售话术")
def generate_scripts(
    payload: ScriptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScriptBundleOut:
    """生成学生微信 / 家长沟通 / 电话提纲三类话术（模板版）。"""
    try:
        bundle = script_service.generate_script_bundle(
            db,
            owner_id=current_user.id,
            course_id=payload.course_id,
            student_id=payload.student_id,
            match_result_id=payload.match_result_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScriptBundleOut(
        student_id=payload.student_id,
        course_id=payload.course_id,
        engine_version="template_v1",
        wechat_student=bundle["wechat_student"],
        parent=bundle["parent"],
        phone_outline=bundle["phone_outline"],
    )


@router.post(
    "/create-task",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="为匹配学生创建跟进待办",
)
def create_match_task(
    payload: CreateMatchTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    from app.models import Course, Student

    course = (
        db.query(Course)
        .filter(Course.id == payload.course_id, Course.owner_id == current_user.id)
        .first()
    )
    student = (
        db.query(Student)
        .filter(Student.id == payload.student_id, Student.owner_id == current_user.id)
        .first()
    )
    if course is None or student is None:
        raise HTTPException(status_code=400, detail="课程或学生不存在")

    title = payload.title or f"课程推荐沟通 · {student.name} · {course.name}"
    try:
        task = task_service.create_task(
            db,
            current_user.id,
            TaskCreate(
                title=title,
                student_id=student.id,
                due_at=None,
                priority="normal",
                status="todo",
                source="match",
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskOut.model_validate(task)
