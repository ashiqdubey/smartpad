"""Application entry point — SPEC.md section 22, step 6.

Sets up:
- loguru logging (rotating file + stderr)
- QApplication
- DB migrations
- WorkerPool
- TrayIcon
- HotkeyListener
- FloatingPanel

Exports run() which is called by __main__.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def _configure_logging(data_dir: Path) -> None:
    """Set up loguru: stderr (INFO+) and rotating file (DEBUG+)."""
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Stderr — INFO and above
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True,
    )

    # Rotating file — DEBUG and above, 10 MB, keep 7
    logger.add(
        log_dir / "smartpad.log",
        level="DEBUG",
        rotation="10 MB",
        retention=7,
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} | {message}",
        enqueue=True,  # thread-safe writes
    )


def run() -> None:
    """Bootstrap and run the SmartPad desktop application."""
    # ── 1. Load settings early (before Qt, to get data dir) ──────────────────
    from smartpad.config import DATA_DIR, load_settings  # noqa: PLC0415

    settings = load_settings()

    # ── 2. Logging ────────────────────────────────────────────────────────────
    _configure_logging(DATA_DIR)
    logger.info("SmartPad starting — data dir: {}", DATA_DIR)

    # ── 3. Run DB migrations ──────────────────────────────────────────────────
    db_path = DATA_DIR / "smartpad.db"
    try:
        from smartpad.db.migrations import run_migrations  # noqa: PLC0415

        run_migrations(db_path)
        logger.info("Migrations complete.")
    except Exception as exc:
        # Non-fatal: app still runs; DB features may not work
        logger.exception("DB migration failed (non-fatal): {}", exc)

    # ── 3b. Initialise async DB engine ────────────────────────────────────────
    try:
        from smartpad.db.engine import init_async_engine  # noqa: PLC0415

        init_async_engine(db_path)
        logger.info("Async DB engine initialised.")
    except Exception as exc:
        logger.exception("Async DB engine init failed (non-fatal): {}", exc)

    # ── 4. QApplication ───────────────────────────────────────────────────────
    from PyQt6.QtWidgets import QApplication  # noqa: PLC0415

    # Prevent app from quitting when last visible window is closed
    # (panel hide should not quit)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("SmartPad")
    app.setApplicationVersion("0.0.1")
    app.setQuitOnLastWindowClosed(False)

    # ── 5. Apply theme ────────────────────────────────────────────────────────
    from smartpad.ui.styles import get_theme  # noqa: PLC0415
    app.setStyleSheet(get_theme(settings.theme))

    # ── 6. Worker pool ────────────────────────────────────────────────────────
    from smartpad.core.worker_pool import WorkerPool  # noqa: PLC0415
    pool = WorkerPool()
    pool.start()
    logger.debug("Worker pool started.")

    # ── 7. Floating panel ─────────────────────────────────────────────────────
    from smartpad.ui.floating_panel import FloatingPanel  # noqa: PLC0415
    panel = FloatingPanel(pool)

    # ── 8. Tray icon ──────────────────────────────────────────────────────────
    from smartpad.ui.tray import TrayIcon  # noqa: PLC0415

    tray = TrayIcon()
    tray.show_panel.connect(panel.toggle_panel)
    tray.quit_requested.connect(app.quit)
    tray.open_settings.connect(lambda: _open_settings(panel))
    tray.open_browse.connect(lambda: _open_browse(panel))
    tray.show()
    logger.debug("Tray icon shown.")

    # ── 8b. Onboarding (first-run) ────────────────────────────────────────────
    try:
        from smartpad.ui.onboarding import OnboardingWizard, needs_onboarding  # noqa: PLC0415

        if needs_onboarding():
            logger.info("First run detected — showing onboarding wizard.")
            wizard = OnboardingWizard()
            wizard.exec()
    except Exception as exc:
        logger.warning("Onboarding check failed (non-fatal): {}", exc)

    # ── 9. Global hotkey ──────────────────────────────────────────────────────
    from smartpad.core.hotkey import HotkeyListener  # noqa: PLC0415

    # pynput combo format: <ctrl>+<alt>+space
    hotkey_combo = _settings_to_pynput(settings.hotkey)

    def _toggle_from_hotkey() -> None:
        # pynput fires on its own thread — QMetaObject.invokeMethod ensures
        # we cross to the Qt main thread safely.
        from PyQt6.QtCore import QMetaObject, Qt  # noqa: PLC0415
        QMetaObject.invokeMethod(
            panel,
            "toggle_panel",
            Qt.ConnectionType.QueuedConnection,
        )

    hotkey_listener = HotkeyListener(
        hotkey_str=hotkey_combo,
        callback=_toggle_from_hotkey,
    )
    hotkey_listener.start()

    # ── 10. Show panel on first launch ────────────────────────────────────────
    panel.show_panel()

    # ── 11. Run event loop ────────────────────────────────────────────────────
    logger.info("SmartPad ready.")
    exit_code = app.exec()

    # ── 12. Cleanup ───────────────────────────────────────────────────────────
    hotkey_listener.stop()
    pool.stop()
    logger.info("SmartPad exited with code {}.", exit_code)
    sys.exit(exit_code)


def _open_settings(parent: object) -> None:
    """Create and show the settings dialog."""
    from smartpad.ui.settings_dialog import SettingsDialog  # noqa: PLC0415

    dlg = SettingsDialog(parent=None)
    dlg.exec()


def _open_browse(parent: object) -> None:
    """Create and show the browse window."""
    from smartpad.ui.browse_window import BrowseWindow  # noqa: PLC0415

    dlg = BrowseWindow(parent=None)
    dlg.exec()


def _settings_to_pynput(hotkey: str) -> str:
    """Convert settings hotkey string to pynput GlobalHotKeys format.

    Settings stores: "ctrl+alt+space"
    pynput expects: "<ctrl>+<alt>+space"

    Single-character keys (letters, digits, space) are left bare;
    modifier/special keys are wrapped in angle brackets.
    """
    _SPECIAL = {
        "ctrl", "alt", "shift", "cmd", "super", "meta",
        "space", "tab", "enter", "return", "esc", "escape",
        "backspace", "delete", "insert", "home", "end",
        "pageup", "pagedown", "up", "down", "left", "right",
        "f1", "f2", "f3", "f4", "f5", "f6",
        "f7", "f8", "f9", "f10", "f11", "f12",
    }
    parts = hotkey.lower().split("+")
    result = []
    for part in parts:
        part = part.strip()
        if part in _SPECIAL or len(part) > 1:
            result.append(f"<{part}>")
        else:
            result.append(part)
    return "+".join(result)
