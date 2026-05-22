from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session

from src.infrastructure.config.settings import settings
from database.models.orm_models import Base

_db_url = settings.database_url
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

_is_sqlite = _db_url.startswith("sqlite")

engine = create_engine(
    _db_url,
    echo=False,
    **({} if _is_sqlite else {"pool_pre_ping": True, "pool_recycle": 1800}),
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(_SessionFactory)


def get_db_session() -> Session:
    return SessionLocal()


def remove_db_session() -> None:
    SessionLocal.remove()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
