"""SQLAlchemy engine + session factory.

Use get_session() as a context manager for all DB access.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from smartpad.db.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _enable_wal_and_fk(engine: Engine) -> None:
    """Enable WAL mode and foreign key enforcement for SQLite."""

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_engine(db_path: Path) -> Engine:
    """Initialise the SQLAlchemy engine for the given SQLite file path."""
    global _engine, _SessionLocal

    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, echo=False, connect_args={"check_same_thread": False})
    _enable_wal_and_fk(engine)
    _engine = engine
    _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("DB engine not initialised. Call init_engine() first.")
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a database session, rolling back on exception."""
    if _SessionLocal is None:
        raise RuntimeError("DB engine not initialised. Call init_engine() first.")
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables(engine: Engine | None = None) -> None:
    """Create all tables defined in models.py (used in tests; prod uses Alembic)."""
    target = engine or get_engine()
    Base.metadata.create_all(target)
