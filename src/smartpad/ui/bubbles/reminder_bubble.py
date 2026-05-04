"""ReminderBubble — displays a saved reminder.

Visual:
- Full-width, amber tint background (BubbleReminder QSS ID)
- clock icon on the left
- Content text
- Time pill: "in X minutes" (if in the future) or absolute formatted time
- After notified: time pill shows "Reminded"

Status dot: top-right corner (saving -> saved -> error).
"""

from __future__ import annotations

from datetime import UTC, datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from smartpad.ui.bubbles.base import BubbleBase


def _format_trigger(trigger_at: datetime | None, notified: bool) -> str:
    """Format the trigger time for the time pill.

    Args:
        trigger_at: The scheduled trigger datetime (timezone-aware preferred).
        notified: Whether the reminder has already fired.

    Returns:
        A human-friendly string for the pill label.
    """
    if notified:
        return "✓ Reminded"

    if trigger_at is None:
        return "—"

    now = datetime.now(UTC)
    if trigger_at.tzinfo is None:
        trigger_utc = trigger_at.replace(tzinfo=UTC)
    else:
        trigger_utc = trigger_at.astimezone(UTC)

    delta_secs = int((trigger_utc - now).total_seconds())

    if delta_secs > 0:
        minutes = delta_secs // 60
        if minutes == 0:
            return "in <1 min"
        if minutes < 60:
            return f"in {minutes} min{'s' if minutes != 1 else ''}"
        hours = minutes // 60
        if hours < 24:
            return f"in {hours}h"
        return trigger_at.strftime("%b %d, %H:%M")

    return trigger_at.strftime("%b %d, %H:%M")


class ReminderBubble(BubbleBase):
    """A saved-reminder bubble.

    Args:
        content: The reminder description text.
        trigger_at: When the reminder should fire.
        notified: Whether the reminder has already fired.
        parent: Optional parent widget.
    """

    def __init__(
        self,
        content: str = "",
        trigger_at: datetime | None = None,
        notified: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._content = content
        self._trigger_at = trigger_at
        self._notified = notified

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        self._bubble_frame = QWidget(self._content_widget)
        self._bubble_frame.setObjectName("BubbleReminder")
        self._bubble_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        frame_layout = QHBoxLayout(self._bubble_frame)
        frame_layout.setContentsMargins(12, 8, 12, 8)
        frame_layout.setSpacing(8)

        self._icon_label = QLabel("⏰")
        self._icon_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        frame_layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        self._content_label = QLabel()
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        frame_layout.addWidget(self._content_label)

        self._time_pill = QLabel()
        self._time_pill.setObjectName("TimePill")
        self._time_pill.setStyleSheet(
            "background-color: rgba(250,179,135,0.25);"
            "color: #fab387;"
            "border-radius: 8px;"
            "padding: 2px 8px;"
            "font-size: 11px;"
        )
        frame_layout.addWidget(self._time_pill)

        self._content_layout.addWidget(self._bubble_frame)

    def set_notified(self, notified: bool = True) -> None:
        """Mark the reminder as fired.

        Args:
            notified: Whether the reminder has been delivered.
        """
        self._notified = notified
        self._refresh()

    def set_content(self, content: str) -> None:
        """Update the reminder text.

        Args:
            content: New reminder description.
        """
        self._content = content
        self._refresh()

    def _refresh(self) -> None:
        self._content_label.setText(self._content)
        self._time_pill.setText(_format_trigger(self._trigger_at, self._notified))
