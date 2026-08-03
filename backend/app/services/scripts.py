"""销售话术模板生成 template_v1。"""

from __future__ import annotations

from app.models import Course, GeneratedScript, Student
from sqlalchemy.orm import Session, selectinload


def _school_text(student: Student) -> str:
    names = [s.school_name for s in (student.schools or []) if s.school_name]
    return "、".join(names[:3]) if names else "目标院校"


def _progress_text(student: Student) -> str:
    if not student.portfolio_started:
        return "作品集尚未系统展开"
    return f"作品集完成度约 {student.portfolio_progress}%"


def generate_script_bundle(
    db: Session,
    *,
    owner_id: int,
    course_id: int,
    student_id: int,
    match_result_id: int | None = None,
) -> dict[str, str]:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.owner_id == owner_id)
        .first()
    )
    student = (
        db.query(Student)
        .options(selectinload(Student.schools), selectinload(Student.tags))
        .filter(Student.id == student_id, Student.owner_id == owner_id)
        .first()
    )
    if course is None:
        raise ValueError("课程不存在或不属于当前账号")
    if student is None:
        raise ValueError("学生不存在或不属于当前账号")

    major = student.major or "艺术"
    stage = student.application_stage or "当前申请"
    schools = _school_text(student)
    progress = _progress_text(student)
    goal = course.goal or "提升申请竞争力"
    course_name = course.name

    wechat_student = (
        f"{student.name}你好，最近学校上线了「{course_name}」。"
        f"我看了一下你目前是{major}方向，目标偏向{schools}，{progress}。"
        f"这门课主要帮助{goal}，和你现在的{stage}阶段比较契合。"
        f"不是一定要报，我先把大纲发你，你看看哪几块最需要补，我们再一起判断要不要进班～"
    )

    parent = (
        f"【学生情况】\n"
        f"{student.name}目前专业方向为{major}，申请阶段处于「{stage}」，{progress}，目标院校方向：{schools}。\n\n"
        f"【为什么建议关注本课程】\n"
        f"「{course_name}」的核心目标是：{goal}。"
        f"结合孩子现阶段节奏，系统课能帮助补齐作品集/申请关键短板，减少临时抱佛脚。\n\n"
        f"【不报名的风险】\n"
        f"若继续按现有节奏推进，可能出现项目完整度不够、差异化不足，或临近网申时集中返工，时间和心态压力都会更大。\n\n"
        f"【课程价值】\n"
        f"课程由{course.teacher_name or '专业老师'}授课，类型为{course.course_type}，"
        f"更强调可执行的阶段目标与反馈，方便家长同步看到进展。\n\n"
        f"您看是否方便本周约 10–15 分钟电话，我按孩子情况说明更细的匹配点。"
    )

    phone_outline = (
        f"1. 开场：确认时间，说明今天只做匹配评估，不强推。\n"
        f"2. 同步学生现状：{major} / {stage} / {progress} / 目标 {schools}。\n"
        f"3. 介绍课程「{course_name}」如何对应短板：{goal}。\n"
        f"4. 说明不推进的风险：临近节点返工、作品集完整度不足。\n"
        f"5. 给出选择：先体验/进班/暂缓，并约定下次跟进时间。\n"
        f"6. 结束：确认家长最关心的问题（效果、时间、价格）。"
    )

    bundle = {
        "wechat_student": wechat_student,
        "parent": parent,
        "phone_outline": phone_outline,
    }

    for channel, content in bundle.items():
        db.add(
            GeneratedScript(
                owner_id=owner_id,
                course_id=course_id,
                student_id=student_id,
                match_result_id=match_result_id,
                channel=channel,
                content=content,
                engine_version="template_v1",
            )
        )
    db.commit()
    return bundle
