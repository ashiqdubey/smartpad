"""pytest configuration — sets QT_QPA_PLATFORM=offscreen before Qt is imported
so UI tests can run in headless environments (CI, WSL, etc.).
"""

import os

# Must be set before any Qt import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
