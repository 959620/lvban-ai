"""AI 助手：OpenAI Chat Completions + 本地兜底。"""

from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.models import Course, Student
from app.schemas import AiStatusOut
from app.services import matching as matching_service
from app.services import scripts as script_service

SYSTEM_PROMPT = """你是艺术留学机构的教务老师智能助手，服务对象是教务老师本人。
请用简洁专业的中文回答，可直接用于工作沟通。
你可以：
1) 根据学生档案分析适合的课程与理由
2) 撰写给学生/家长的沟通话术（自然、不强推）
3) 总结申请进度并给出下一步行动建议
若上下文信息不足，请明确指出还需要哪些字段。
不要编造不存在的院校录取结果或虚假数据。"""


def get_ai_status() -> AiStatusOut:
    settings = get_settings()
    configured = bool(settings.openai_api_key.strip())
    return AiStatusOut(
        configured=configured,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        message="已配置大模型接口，将调用真实模型"
        if configured
        else "尚未配置 OPENAI_API_KEY：将使用本地规则兜底（匹配/话术模板）",
    )


def _student_context(student: Student) -> dict[str, Any]:
    return {
        "id": student.id,
        "name": student.name,
        "grade": student.grade,
        "major": student.major,
        "target_country": student.target_country,
        "target_major": student.target_major,
        "intake_year": student.intake_year,
        "application_stage": student.application_stage,
        "portfolio_started": student.portfolio_started,
        "portfolio_project_count": student.portfolio_project_count,
        "portfolio_progress": student.portfolio_progress,
        "schools": [
            {"name": s.school_name, "priority": s.priority} for s in (student.schools or [])
        ],
        "tags": [t.name for t in (student.tags or [])],
        "personality_notes": student.personality_notes,
        "communication_notes": student.communication_notes,
        "next_contact_at": student.next_contact_at.isoformat() if student.next_contact_at else None,
    }


def _course_context(course: Course) -> dict[str, Any]:
    return {
        "id": course.id,
        "name": course.name,
        "course_type": course.course_type,
        "suitable_majors": course.suitable_majors or [],
        "suitable_stages": course.suitable_stages or [],
        "goal": course.goal,
        "price": str(course.price) if course.price is not None else None,
        "teacher_name": course.teacher_name,
        "description": course.description,
    }


def build_context(
    db: Session,
    *,
    owner_id: int,
    student_id: int | None,
    course_id: int | None,
) -> dict[str, Any]:
    context: dict[str, Any] = {"owner_id": owner_id, "student": None, "course": None, "courses": []}

    if student_id is not None:
        student = (
            db.query(Student)
            .options(selectinload(Student.schools), selectinload(Student.tags))
            .filter(Student.id == student_id, Student.owner_id == owner_id)
            .first()
        )
        if student is None:
            raise ValueError("学生不存在或不属于当前账号")
        context["student"] = _student_context(student)

    if course_id is not None:
        course = (
            db.query(Course)
            .filter(Course.id == course_id, Course.owner_id == owner_id)
            .first()
        )
        if course is None:
            raise ValueError("课程不存在或不属于当前账号")
        context["course"] = _course_context(course)

    # 提供名下课程摘要，便于“适合什么课程”类问题
    courses = (
        db.query(Course)
        .filter(Course.owner_id == owner_id)
        .order_by(Course.updated_at.desc())
        .limit(30)
        .all()
    )
    context["courses"] = [_course_context(item) for item in courses]
    return context


def _call_openai(message: str, context: dict[str, Any]) -> str:
    settings = get_settings()
    payload = {
        "model": settings.openai_model,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": "以下是当前业务上下文 JSON，请优先依据这些数据回答：\n"
                + json.dumps(context, ensure_ascii=False),
            },
            {"role": "user", "content": message},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            detail = response.text[:500]
            raise RuntimeError(f"OpenAI 调用失败（{response.status_code}）：{detail}")
        data = response.json()

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise RuntimeError("OpenAI 返回格式异常") from exc


def _local_fallback(db: Session, message: str, context: dict[str, Any], owner_id: int) -> str:
    text = message.strip()
    student = context.get("student")
    course = context.get("course")

    # 有学生：适合什么课程 → 对每门课跑匹配分（简化：直接对选中学生解释 + 列出高分课）
    if student and any(key in text for key in ["适合什么课", "推荐课程", "匹配课程", "什么课程"]):
        courses = context.get("courses") or []
        if not courses:
            return "当前账号下还没有课程。请先在「课程库」新建课程，再来分析匹配。"
        lines = [
            f"【本地规则分析】学生 {student['name']}（{student.get('major') or '专业未填'} / "
            f"{student.get('application_stage') or '阶段未填'} / 作品集 {student.get('portfolio_progress', 0)}%）",
            "",
        ]
        ranked: list[tuple[float, dict[str, Any], list[str]]] = []
        student_obj = (
            db.query(Student)
            .options(selectinload(Student.schools), selectinload(Student.tags))
            .filter(Student.id == student["id"], Student.owner_id == owner_id)
            .first()
        )
        for item in courses:
            course_obj = (
                db.query(Course)
                .filter(Course.id == item["id"], Course.owner_id == owner_id)
                .first()
            )
            if student_obj is None or course_obj is None:
                continue
            score, reasons = matching_service.score_student_for_course(course_obj, student_obj)
            ranked.append((score, item, reasons))
        ranked.sort(key=lambda x: -x[0])
        for score, item, reasons in ranked[:5]:
            lines.append(f"- {item['name']}（{score:.0f} 分）")
            for reason in reasons[:2]:
                lines.append(f"  · {reason}")
        lines.append("")
        lines.append("提示：配置 OPENAI_API_KEY 后可获得更自然的综合建议与话术润色。")
        return "\n".join(lines)

    # 有学生+课程，或要求话术
    if any(key in text for key in ["话术", "家长", "微信", "电话"]):
        if not student:
            return "请先在上方选择学生，我才能生成针对性话术。"
        target_course_id = course["id"] if course else None
        if target_course_id is None and context.get("courses"):
            target_course_id = context["courses"][0]["id"]
        if target_course_id is None:
            return "请先选择课程，或在课程库中创建课程后再生成话术。"
        bundle = script_service.generate_script_bundle(
            db,
            owner_id=owner_id,
            course_id=target_course_id,
            student_id=student["id"],
        )
        return (
            "【本地模板话术】\n\n"
            "一、给学生微信\n"
            f"{bundle['wechat_student']}\n\n"
            "二、给家长\n"
            f"{bundle['parent']}\n\n"
            "三、电话提纲\n"
            f"{bundle['phone_outline']}\n\n"
            "提示：配置 OPENAI_API_KEY 后可按你的语气进一步改写。"
        )

    if student and any(key in text for key in ["进度", "总结", "情况"]):
        schools = "、".join(s["name"] for s in student.get("schools") or []) or "未填写"
        tags = "、".join(student.get("tags") or []) or "无"
        return (
            f"【学生速览】{student['name']}\n"
            f"- 专业：{student.get('major') or '未填'}\n"
            f"- 阶段：{student.get('application_stage') or '未填'}\n"
            f"- 目标国家/专业：{student.get('target_country') or '未填'} / {student.get('target_major') or '未填'}\n"
            f"- 入学年：{student.get('intake_year') or '未填'}\n"
            f"- 作品集：{'已开始' if student.get('portfolio_started') else '未开始'}，"
            f"完成度 {student.get('portfolio_progress', 0)}%，项目数 {student.get('portfolio_project_count', 0)}\n"
            f"- 目标院校：{schools}\n"
            f"- 标签：{tags}\n"
            f"- 下次联系：{student.get('next_contact_at') or '未设置'}\n\n"
            "建议下一步：补充跟进记录，并在「课程匹配」中跑一次推荐。"
        )

    return (
        "尚未配置 OPENAI_API_KEY，当前为本地兜底模式。\n"
        "你可以：\n"
        "1) 选择学生后问「分析适合什么课程」\n"
        "2) 选择学生（和课程）后问「帮我写家长沟通话术」\n"
        "3) 选择学生后问「总结申请进度」\n\n"
        f"你刚才问的是：{text}\n\n"
        "在 backend/.env 设置 OPENAI_API_KEY 后即可启用真实大模型。"
    )


def run_assistant(
    db: Session,
    *,
    message: str,
    student_id: int | None,
    course_id: int | None,
    owner_id: int,
) -> dict:
    settings = get_settings()
    status = get_ai_status()
    context = build_context(
        db,
        owner_id=owner_id,
        student_id=student_id,
        course_id=course_id,
    )

    if not status.configured:
        reply = _local_fallback(db, message, context, owner_id)
        return {
            "engine": "local_fallback",
            "reply": reply,
            "context": {
                "owner_id": owner_id,
                "student_id": student_id,
                "course_id": course_id,
                "has_student": context["student"] is not None,
                "has_course": context["course"] is not None,
                "course_count": len(context["courses"]),
            },
            "model": "local",
        }

    try:
        reply = _call_openai(message, context)
        engine = "openai"
        model = settings.openai_model
    except Exception as exc:  # noqa: BLE001 - 返回可读错误给前端
        # 模型失败时降级本地，避免工作中断
        reply = (
            f"OpenAI 调用失败：{exc}\n\n"
            "已自动切换到本地兜底结果：\n\n"
            + _local_fallback(db, message, context, owner_id)
        )
        engine = "openai_fallback_local"
        model = settings.openai_model

    return {
        "engine": engine,
        "reply": reply,
        "context": {
            "owner_id": owner_id,
            "student_id": student_id,
            "course_id": course_id,
            "has_student": context["student"] is not None,
            "has_course": context["course"] is not None,
            "course_count": len(context["courses"]),
        },
        "model": model,
    }
