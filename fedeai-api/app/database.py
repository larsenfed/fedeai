from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


database_url = settings.database_url
if database_url.startswith("postgres://"):
    # Heroku Postgres may provide the legacy postgres:// scheme.
    # SQLAlchemy 2 expects postgresql://.
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine_kwargs = {"pool_pre_ping": True}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
