"""System tray icon — SPEC.md section 12.

TrayIcon wraps QSystemTrayIcon with:
- A simple 16x16 coloured-square icon (Phase 23 adds the real icon)
- Context menu: Open SmartPad | separator | Quit
- Double-click and menu "Open" both emit show_panel signal
"""

from __future__ import annotations

from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class TrayIcon(QObject):
    """System tray icon that emits Qt signals to the rest of the UI."""

    show_panel = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this platform.")

        self._tray = QSystemTrayIcon(self._make_icon(), self)
        self._tray.setToolTip("SmartPad")

        menu = QMenu()
        open_action = menu.addAction("Open SmartPad")
        menu.addSeparator()
        quit_action = menu.addAction("Quit")

        self._tray.setContextMenu(menu)

        # Connections
        open_action.triggered.connect(self.show_panel)
        quit_action.triggered.connect(self.quit_requested)
        self._tray.activated.connect(self._on_activated)

    # ── Public interface ──────────────────────────────────────────────────────

    def show(self) -> None:
        """Make the tray icon visible."""
        self._tray.show()
        logger.debug("Tray icon shown.")

    def hide(self) -> None:
        """Remove the tray icon."""
        self._tray.hide()

    def show_notification(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        duration_ms: int = 5000,
    ) -> None:
        """Show a platform notification bubble via the tray."""
        self._tray.showMessage(title, message, icon, duration_ms)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _make_icon() -> QIcon:
        """Create a simple 16x16 magenta square icon (placeholder)."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#89b4fa"))  # accent blue from dark theme
        return QIcon(pixmap)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_panel.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single-click on some platforms (e.g. Windows)
            pass
