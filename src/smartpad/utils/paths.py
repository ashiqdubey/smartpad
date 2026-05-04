"""Platform-specific data directory resolution.

Always use get_data_dir() instead of constructing paths manually.
Respects XDG_DATA_HOME on Linux, standard conventions on Windows/macOS.
"""

import os
import sys
from pathlib import Path


def get_data_dir() -> Path:
    """Return the platform-appropriate application data directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "smartpad"
        return Path.home() / "AppData" / "Roaming" / "smartpad"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "smartpad"

    # Linux / other POSIX
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "smartpad"
    return Path.home() / ".local" / "share" / "smartpad"
