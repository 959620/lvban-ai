"""课程匹配规则引擎 rule_v1。"""

from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session, selectinload

from app.models import Course, MatchResult, MatchRun, Student

# 课程「相对阶段」映射到学生申请阶段
STAGE_ALIASES: dict[str, set[str]] = {
    "申请前6个月": {"选校规划", "作品集制作", "意向确认"},
    "申请前3个月": {"作品集制作", "文书准备", "网申提交"},
    "临近网申": {"文书准备", "网申提交", "面试/作品集面试"},
}

PUSH_TAGS = {"拖延严重", "需要强督促", "家长关注度高"}


def _course_text(course: Course) -> str:
    parts = [course.name or "", course.goal or "", course.description or ""]
    return " ".join(parts).lower()


def score_student_for_course(course: Course, student: Student) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    majors = set(course.suitable_majors or [])
    stages = set(course.suitable_stages or [])
    text = _course_text(course)

    # 1. 专业命中
    if student.major and student.major in majors:
        score += 30
        reasons.append(f"专业匹配：{student.major}")
    elif student.major and majors:
        score += 5
        reasons.append(f"专业为{student.major}，与课程目标专业不完全一致，可酌情沟通")
    elif not majors:
        score += 10

    # 2. 申请阶段命中（含相对阶段别名）
    expanded_stages: set[str] = set()
    for stage in stages:
        expanded_stages.add(stage)
        expanded_stages |= STAGE_ALIASES.get(stage, set())

    if student.application_stage and student.application_stage in expanded_stages:
        score += 25
        reasons.append(f"当前阶段「{student.application_stage}」适合本课程")
    elif student.application_stage and stages:
        score += 5
        reasons.append(f"当前阶段为「{student.application_stage}」，可关注是否进入适合窗口")

    # 3. 作品集完成度
    progress = student.portfolio_progress or 0
    portfolio_related = any(key in text for key in ["作品集", "portfolio", "项目"])
    if portfolio_related or "作品集" in (course.goal or ""):
        if 40 <= progress <= 80:
            score += 20
            reasons.append(f"作品集完成度 {progress}%，正处于可强化提升区间")
        elif 20 <= progress < 40:
            score += 12
            reasons.append(f"作品集完成度 {progress}%，适合通过课程加快启动与成型")
        elif progress > 80:
            score += 8
            reasons.append(f"作品集完成度已达 {progress}%，可用于冲刺打磨与差异化提升")
        elif student.portfolio_started:
            score += 6
            reasons.append("已开始作品集，可借课程建立节奏")
        else:
            score += 4
            reasons.append("尚未深入作品集，可评估是否需要系统课启动")

    # 4. 目标院校关键词
    school_names = [s.school_name for s in (student.schools or []) if s.school_name]
    for school in school_names:
        token = school.strip()
        if len(token) >= 2 and token.lower() in text:
            score += 18
            reasons.append(f"目标院校「{school}」与课程定位相关")
            break
        # 常见缩写：课程名含 RISD，院校也写 Rhode Island...
        abbrev = re.sub(r"[^A-Za-z]", "", token)
        if len(abbrev) >= 3 and abbrev.lower() in text:
            score += 15
            reasons.append(f"目标院校关键词与课程名称相关（{school}）")
            break

    # 5. 标签加权
    tag_names = {t.name for t in (student.tags or [])}
    hit_tags = sorted(tag_names & PUSH_TAGS)
    if hit_tags:
        score += 8 * len(hit_tags)
        reasons.append("学生标签提示需加强督促/家长沟通：" + "、".join(hit_tags))
    if "有艺术基础" in tag_names:
        score += 4
        reasons.append("具备艺术基础，课程吸收效率可能更高")
    if "英语薄弱" in tag_names and any(k in text for k in ["英语", "文书", "面试", "托福", "雅思"]):
        score += 6
        reasons.append("英语薄弱且课程涉及相关能力，可重点关注")

    # 6. 入学年份临近（粗略）
    if student.intake_year:
        # 不依赖当前年硬编码过多；有入学年即略加权
        score += 3
        reasons.append(f"计划 {student.intake_year} 入学，时间规划需紧凑")

    score = min(score, 100.0)
    if not reasons:
        reasons.append("综合信息有限，建议人工复核后再沟通")
    return score, reasons


def run_course_match(
    db: Session,
    *,
    owner_id: int,
    course_id: int,
    min_score: float = 25,
) -> MatchRun:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.owner_id == owner_id)
        .first()
    )
    if course is None:
        raise ValueError("课程不存在或不属于当前账号")

    students = (
        db.query(Student)
        .options(selectinload(Student.schools), selectinload(Student.tags))
        .filter(Student.owner_id == owner_id)
        .all()
    )

    scored: list[tuple[Student, float, list[str]]] = []
    for student in students:
        score, reasons = score_student_for_course(course, student)
        if score >= min_score:
            scored.append((student, score, reasons))

    scored.sort(key=lambda item: (-item[1], item[0].name))

    run = MatchRun(owner_id=owner_id, course_id=course.id, engine_version="rule_v1")
    db.add(run)
    db.flush()

    for index, (student, score, reasons) in enumerate(scored, start=1):
        db.add(
            MatchResult(
                run_id=run.id,
                student_id=student.id,
                score=round(score, 1),
                rank=index,
                reasons=json.dumps(reasons, ensure_ascii=False),
            )
        )

    db.commit()
    return get_match_run(db, run.id, owner_id)  # type: ignore[return-value]


def get_match_run(db: Session, run_id: int, owner_id: int) -> MatchRun | None:
    return (
        db.query(MatchRun)
        .options(
            selectinload(MatchRun.course),
            selectinload(MatchRun.results).selectinload(MatchResult.student).selectinload(Student.schools),
            selectinload(MatchRun.results).selectinload(MatchResult.student).selectinload(Student.tags),
        )
        .filter(MatchRun.id == run_id, MatchRun.owner_id == owner_id)
        .first()
    )
