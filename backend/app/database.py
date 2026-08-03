from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401
    from app.services.students import seed_preset_tags

    # SQLite 落盘目录（如 Zeabur 挂载的 /data）
    if settings.database_url.startswith("sqlite"):
        raw = settings.database_url.replace("sqlite:///", "", 1)
        db_path = Path(raw)
        if str(db_path.parent) not in {"", "."}:
            db_path.parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_preset_tags(db)
    finally:
        db.close()
