"""ErrorBubble — displays an error message with a retry button.

Visual:
- Full-width, red tint background (BubbleError QSS ID)
- ⚠️ icon on the left
- Error message text
- "Retry" QPushButton that emits ``retry_requested`` signal

Status dot: top-right corner (saving → saved → error).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from smartpad.ui.bubbles.base import BubbleBase


class ErrorBubble(BubbleBase):
    """An error bubble with a retry action.

    Signals:
        retry_requested: Emitted when the user clicks the "Retry" button.

    Args:
        message: The error description to display.
        parent: Optional parent widget.
    """

    retry_requested = pyqtSignal()

    def __init__(
        self,
        message: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._message = message

        self._build_ui()
        self._refresh()
        # Errors always start in error state
        self.set_status("error")

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._bubble_frame = QWidget(self._content_widget)
        self._bubble_frame.setObjectName("BubbleError")
        self._bubble_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        frame_layout = QHBoxLayout(self._bubble_frame)
        frame_layout.setContentsMargins(12, 8, 12, 8)
        frame_layout.setSpacing(8)

        # ⚠️ icon
        self._icon_label = QLabel("⚠️")
        self._icon_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        frame_layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        # Error message text
        self._message_label = QLabel()
        self._message_label.setWordWrap(True)
        self._message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._message_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        frame_layout.addWidget(self._message_label)

        # Retry button
        self._retry_btn = QPushButton("Retry")
        self._retry_btn.setObjectName("RetryButton")
        self._retry_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: rgba(243,139,168,0.20);"
            "  color: #f38ba8;"
            "  border: 1px solid #f38ba8;"
            "  border-radius: 6px;"
            "  padding: 4px 12px;"
            "  font-size: 12px;"
            "}"
            "QPushButton:hover {"
            "  background-color: rgba(243,139,168,0.35);"
            "}"
        )
        self._retry_btn.clicked.connect(self.retry_requested.emit)
        frame_layout.addWidget(self._retry_btn)

        self._content_layout.addWidget(self._bubble_frame)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_message(self, message: str) -> None:
        """Update the displayed error message.

        Args:
            message: New error text.
        """
        self._message = message
        self._refresh()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._message_label.setText(self._message)
