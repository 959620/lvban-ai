"""
数据库引擎与会话管理。

设计原因：
- 统一 Session 生命周期，避免在 API 层直接操作引擎
- SQLite 连接参数集中配置，方便以后切 PostgreSQL
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import BASE_DIR, get_settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


settings = get_settings()

# SQLite 需关闭同线程检查，便于 FastAPI 多线程访问
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends 用的会话生成器。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据目录并创建表结构。"""
    (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)

    # 导入模型以注册 metadata（Step 4 起启用建表）
    from app.models import notification_log, reminder, student, task  # noqa: F401

    Base.metadata.create_all(bind=engine)
