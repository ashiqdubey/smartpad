"""SQLAlchemy engine + session factory (sync for Alembic, async for repositories).

Sync:   init_engine() / get_session()   — used by Alembic migrations and tests
Async:  init_async_engine() / get_async_session() — used by repositories at runtime
"""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from smartpad.db.models import Base

# --- Sync (Alembic / migrations) ---
_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None

# --- Async (repositories / runtime) ---
_async_engine: AsyncEngine | None = None
_AsyncSessionLocal: sessionmaker[AsyncSession] | None = None  # type: ignore[type-arg]


def _enable_wal_and_fk(engine: Engine) -> None:
    """Enable WAL mode and foreign-key enforcement for a sync SQLite engine."""

    @event.listens_for(engine, "connect")
    def set_pragma(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ── Sync ─────────────────────────────────────────────────────────────────────

def init_engine(db_path: Path) -> Engine:
    """Initialise the sync SQLAlchemy engine (used by Alembic and tests)."""
    global _engine, _SessionLocal
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    _enable_wal_and_fk(engine)
    _engine = engine
    _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Sync DB engine not initialised. Call init_engine() first.")
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a sync session, rolling back on exception."""
    if _SessionLocal is None:
        raise RuntimeError("Sync DB engine not initialised. Call init_engine() first.")
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Async ────────────────────────────────────────────────────────────────────

def init_async_engine(db_path: Path) -> AsyncEngine:
    """Initialise the async SQLAlchemy engine (used by repositories at runtime)."""
    global _async_engine, _AsyncSessionLocal
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    _async_engine = engine
    _AsyncSessionLocal = sessionmaker(  # type: ignore[call-overload]
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine


def get_async_engine() -> AsyncEngine:
    if _async_engine is None:
        raise RuntimeError("Async DB engine not initialised. Call init_async_engine() first.")
    return _async_engine


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session, rolling back on exception."""
    if _AsyncSessionLocal is None:
        raise RuntimeError("Async DB engine not initialised. Call init_async_engine() first.")
    session: AsyncSession = _AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# ── Utilities ─────────────────────────────────────────────────────────────────

def create_tables(engine: Engine | None = None) -> None:
    """Create all ORM tables (tests only; production uses Alembic)."""
    Base.metadata.create_all(engine or get_engine())
