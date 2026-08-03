from sqlalchemy.orm import Session, selectinload

from app.constants import PRESET_TAGS
from app.models import Student, StudentSchool, Tag
from app.schemas import StudentCreate, StudentUpdate


def seed_preset_tags(db: Session) -> None:
    existing = {tag.name for tag in db.query(Tag).all()}
    created = False
    for item in PRESET_TAGS:
        if item["name"] in existing:
            continue
        db.add(Tag(name=item["name"], category=item["category"]))
        created = True
    if created:
        db.commit()


def get_owned_student(db: Session, student_id: int, owner_id: int) -> Student | None:
    return (
        db.query(Student)
        .options(selectinload(Student.schools), selectinload(Student.tags))
        .filter(Student.id == student_id, Student.owner_id == owner_id)
        .first()
    )


def list_owned_students(
    db: Session,
    owner_id: int,
    *,
    q: str | None = None,
    major: str | None = None,
    application_stage: str | None = None,
    tag_id: int | None = None,
    intake_year: int | None = None,
) -> list[Student]:
    query = (
        db.query(Student)
        .options(selectinload(Student.schools), selectinload(Student.tags))
        .filter(Student.owner_id == owner_id)
    )

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (Student.name.ilike(like))
            | (Student.major.ilike(like))
            | (Student.target_country.ilike(like))
            | (Student.target_major.ilike(like))
        )
    if major:
        query = query.filter(Student.major == major)
    if application_stage:
        query = query.filter(Student.application_stage == application_stage)
    if intake_year is not None:
        query = query.filter(Student.intake_year == intake_year)
    if tag_id is not None:
        query = query.filter(Student.tags.any(Tag.id == tag_id))

    return query.order_by(Student.updated_at.desc(), Student.id.desc()).all()


def _resolve_tags(db: Session, tag_ids: list[int]) -> list[Tag]:
    if not tag_ids:
        return []
    tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    if len(tags) != len(set(tag_ids)):
        raise ValueError("存在无效标签")
    return tags


def create_student(db: Session, owner_id: int, payload: StudentCreate) -> Student:
    tags = _resolve_tags(db, payload.tag_ids)
    data = payload.model_dump(exclude={"schools", "tag_ids"})
    student = Student(owner_id=owner_id, **data)
    student.tags = tags
    student.schools = [
        StudentSchool(school_name=school.school_name.strip(), priority=school.priority)
        for school in payload.schools
        if school.school_name.strip()
    ]
    db.add(student)
    db.commit()
    return get_owned_student(db, student.id, owner_id)  # type: ignore[return-value]


def update_student(db: Session, student: Student, payload: StudentUpdate) -> Student:
    tags = _resolve_tags(db, payload.tag_ids)
    data = payload.model_dump(exclude={"schools", "tag_ids"})
    for key, value in data.items():
        setattr(student, key, value)

    student.tags = tags
    student.schools.clear()
    for school in payload.schools:
        name = school.school_name.strip()
        if not name:
            continue
        student.schools.append(StudentSchool(school_name=name, priority=school.priority))

    db.add(student)
    db.commit()
    return get_owned_student(db, student.id, student.owner_id)  # type: ignore[return-value]


def delete_student(db: Session, student: Student) -> None:
    db.delete(student)
    db.commit()
