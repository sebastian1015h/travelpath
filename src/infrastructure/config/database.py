from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.infrastructure.config.settings import settings
from database.models.orm_models import Base

_db_url = settings.database_url
# Render/Heroku entregan postgres:// pero SQLAlchemy 2.x requiere postgresql://
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

_is_sqlite = _db_url.startswith("sqlite")

engine = create_engine(
    _db_url,
    echo=settings.flask_debug,
    **({} if _is_sqlite else {"pool_pre_ping": True, "pool_recycle": 3600}),
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    return SessionLocal()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
