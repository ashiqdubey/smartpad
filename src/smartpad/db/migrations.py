"""Alembic migration runner invoked at app startup."""

from pathlib import Path

from alembic.config import Config

from alembic import command


def run_migrations(db_path: Path) -> None:
    """Run all pending Alembic migrations against the given DB path."""
    project_root = Path(__file__).resolve().parents[3]
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    command.upgrade(alembic_cfg, "head")
