"""Portable-mode detection.

When the app runs from a portable distribution (zip), data lives next to the
executable rather than in the OS application data directory.
"""

import sys
from pathlib import Path


def is_portable() -> bool:
    """Return True if running in portable mode."""
    exe_dir = Path(sys.executable).parent
    return (exe_dir / "portable.txt").exists() or (exe_dir / "smartpad.db").exists()


def get_portable_dir() -> Path | None:
    """Return the portable data directory, or None if not portable."""
    if is_portable():
        return Path(sys.executable).parent
    return None
