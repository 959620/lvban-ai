from sqlalchemy.orm import Session

from app.models import Course
from app.schemas.course import CourseCreate, CourseUpdate


def list_courses(
    db: Session,
    owner_id: int,
    *,
    q: str | None = None,
    course_type: str | None = None,
    major: str | None = None,
    stage: str | None = None,
) -> list[Course]:
    query = db.query(Course).filter(Course.owner_id == owner_id)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (Course.name.ilike(like))
            | (Course.teacher_name.ilike(like))
            | (Course.goal.ilike(like))
        )
    if course_type:
        query = query.filter(Course.course_type == course_type)

    items = query.order_by(Course.updated_at.desc(), Course.id.desc()).all()

    # JSON 字段筛选在应用层处理，兼容 SQLite
    if major:
        items = [item for item in items if major in (item.suitable_majors or [])]
    if stage:
        items = [item for item in items if stage in (item.suitable_stages or [])]
    return items


def get_owned_course(db: Session, course_id: int, owner_id: int) -> Course | None:
    return db.query(Course).filter(Course.id == course_id, Course.owner_id == owner_id).first()


def create_course(db: Session, owner_id: int, payload: CourseCreate) -> Course:
    course = Course(owner_id=owner_id, **payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course: Course, payload: CourseUpdate) -> Course:
    for key, value in payload.model_dump().items():
        setattr(course, key, value)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()
