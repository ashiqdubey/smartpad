"""BubbleBase — common base class for all bubble widget types.

Provides:
- Status dot (8px circle: grey=saving, green=saved, red=error) overlaid top-right
- Common margin/padding constants (8px horizontal, 6px vertical)
- created_at timestamp
- set_status() to update the dot
"""

from __future__ import annotations

from datetime import UTC, datetime

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

# ── Constants ─────────────────────────────────────────────────────────────────

BUBBLE_MARGIN_H = 8   # horizontal margin (px)
BUBBLE_MARGIN_V = 6   # vertical margin (px)
STATUS_DOT_SIZE = 8   # diameter of the status dot (px)

# Status → colour mapping (hex strings)
_STATUS_COLOURS: dict[str, str] = {
    "saving": "#888888",  # grey
    "saved": "#40c070",   # green
    "error": "#f38ba8",   # red (matches bubble-error accent from styles.py)
}


class _StatusDot(QWidget):
    """Tiny 8×8 circle that shows save status.

    Colours:
        saving → grey (#888888)
        saved  → green (#40c070)
        error  → red (#f38ba8)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colour = QColor(_STATUS_COLOURS["saving"])
        self.setFixedSize(QSize(STATUS_DOT_SIZE, STATUS_DOT_SIZE))
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_colour(self, hex_colour: str) -> None:
        """Update the dot colour and repaint."""
        self._colour = QColor(hex_colour)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._colour)
        painter.drawEllipse(0, 0, STATUS_DOT_SIZE, STATUS_DOT_SIZE)
        painter.end()


class BubbleBase(QWidget):
    """Abstract base for all SmartPad bubble widgets.

    Subclasses should call ``super().__init__()`` and then build their own
    layout inside ``self._content_widget`` (already added to the root layout).

    The status dot is overlaid in the top-right corner of the bubble via an
    absolute-positioned child widget that is re-positioned on resize.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status: str = "saving"
        self.created_at: datetime = datetime.now(UTC)

        # Root layout: adds horizontal margins and a thin vertical padding
        root = QVBoxLayout(self)
        root.setContentsMargins(BUBBLE_MARGIN_H, BUBBLE_MARGIN_V, BUBBLE_MARGIN_H, BUBBLE_MARGIN_V)
        root.setSpacing(0)

        # Content area — subclasses populate this
        self._content_widget = QWidget(self)
        self._content_layout = QHBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(4)
        root.addWidget(self._content_widget)

        # Status dot — child of *self* so it floats above content
        self._dot = _StatusDot(self)
        self._reposition_dot()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def status(self) -> str:
        """Current status: 'saving' | 'saved' | 'error'."""
        return self._status

    def set_status(self, status: str) -> None:
        """Update status and repaint the indicator dot.

        Args:
            status: One of ``'saving'``, ``'saved'``, or ``'error'``.
        """
        if status not in _STATUS_COLOURS:
            return
        self._status = status
        self._dot.set_colour(_STATUS_COLOURS[status])

    # ── Qt overrides ──────────────────────────────────────────────────────────

    def resizeEvent(self, event: object) -> None:  # noqa: N802
        super().resizeEvent(event)  # type: ignore[arg-type]
        self._reposition_dot()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _reposition_dot(self) -> None:
        """Place the status dot at the top-right corner with a 4px margin."""
        margin = 4
        x = self.width() - STATUS_DOT_SIZE - margin
        y = margin
        self._dot.move(x, y)
        self._dot.raise_()
