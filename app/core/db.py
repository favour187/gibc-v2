from __future__ import annotations
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import DateTime, create_engine, event, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from .logging import get_logger

logger = get_logger("app.db")

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        text = dt.isoformat()
        return text if text.endswith("Z") else f"{text }Z"
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class Base(DeclarativeBase):
    pass

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

class TimestampsMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

def _ensure_sqlite_dir(database_url: str) -> None:
    if database_url.startswith("sqlite:///"):
        path = database_url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://") :]
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgresql://") :]
    return database_url

def database_backend(database_url: str) -> str:
    return normalize_database_url(database_url).split(":", 1)[0].split("+", 1)[0]

def make_engine(database_url: str, *, echo: bool = False) -> Engine:
    database_url = normalize_database_url(database_url)
    _ensure_sqlite_dir(database_url)
    kwargs: dict = {"echo": echo, "future": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=5)
    engine = create_engine(database_url, **kwargs)
    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine

def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def init_db(engine: Engine) -> None:
    from . import auth

    Base.metadata.create_all(engine)
    logger.info("Database tables ensured: %s", sorted(Base.metadata.tables))

def get_db() -> Iterator[Session]:
    from .state import get_app_state

    factory = get_app_state().session_factory
    if factory is None:
        raise RuntimeError("Database not initialised (session_factory is None)")
    with factory() as session:
        yield session

@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
