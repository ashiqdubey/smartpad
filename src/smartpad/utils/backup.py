"""Auto-backup utilities — SPEC.MD section 20.

Daily backup of the SQLite DB to <data_dir>/backups/.
Keeps only the last N copies (default 7).
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger


def should_backup_today(data_dir: Path) -> bool:
    """Return True if no backup exists for today's date."""
    backup_dir = data_dir / "backups"
    if not backup_dir.exists():
        return True
    today = datetime.now().strftime("%Y-%m-%d")
    return not any(backup_dir.glob(f"smartpad-{today}.db"))


def daily_backup(data_dir: Path, db_path: Path, retention: int = 7) -> Path | None:
    """Copy the DB to backups/ and prune old copies.

    Returns the path of the new backup file, or None on failure.
    """
    backup_dir = data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    dest = backup_dir / f"smartpad-{today}.db"

    try:
        shutil.copy2(db_path, dest)
        logger.info("Backup created: {}", dest)
    except Exception as exc:
        logger.error("Backup failed: {}", exc)
        return None

    _prune_backups(backup_dir, retention)
    return dest


def _prune_backups(backup_dir: Path, keep: int) -> None:
    """Delete oldest backups beyond the keep limit."""
    backups = sorted(backup_dir.glob("smartpad-*.db"))
    to_delete = backups[: max(0, len(backups) - keep)]
    for old in to_delete:
        try:
            old.unlink()
            logger.debug("Pruned old backup: {}", old)
        except Exception as exc:
            logger.warning("Could not delete old backup {}: {}", old, exc)
