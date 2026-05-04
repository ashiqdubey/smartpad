"""Crash recovery — SPEC.MD section 20.

Writes a .recovery file before each chat send.
On next launch, if the file exists, restores the last 5 messages.
Always on, no toggle.
"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

_RECOVERY_FILENAME = ".recovery"


def write_recovery(data_dir: Path, messages: list[dict]) -> None:
    """Persist recent messages to .recovery (called before each send)."""
    path = data_dir / _RECOVERY_FILENAME
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(messages[-5:]), encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not write recovery file: {}", exc)


def read_recovery(data_dir: Path) -> list[dict] | None:
    """Return recovered messages from the previous session, or None."""
    path = data_dir / _RECOVERY_FILENAME
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else None
    except Exception as exc:
        logger.warning("Could not read recovery file: {}", exc)
        return None


def clear_recovery(data_dir: Path) -> None:
    """Delete the recovery file after successful restore."""
    path = data_dir / _RECOVERY_FILENAME
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        logger.warning("Could not clear recovery file: {}", exc)
