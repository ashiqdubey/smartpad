"""ChatBubble — displays user and AI chat messages.

User messages:
- Right-aligned, accent blue background, white text, max 80% width

AI messages:
- Left-aligned, neutral background
- Streaming cursor (| blinking) while generating
- finish_streaming() removes the cursor

Status dot: tiny circle top-right (saving -> saved -> error).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from smartpad.ui.bubbles.base import BubbleBase


class ChatBubble(BubbleBase):
    """A single chat message bubble (user or AI).

    Args:
        role: 'user' or 'assistant' (any non-user value is treated as AI).
        text: Initial message content.
        streaming: If True, the cursor blink animation starts immediately.
        parent: Optional parent widget.
    """

    _BLINK_MS = 500

    def __init__(
        self,
        role: str = "user",
        text: str = "",
        streaming: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._role = role
        self._streaming = False
        self._cursor_visible = False
        self._base_text = text

        self._build_ui()

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(self._BLINK_MS)
        self._blink_timer.timeout.connect(self._toggle_cursor)

        if text:
            self.set_content(text, streaming=streaming)
        elif streaming:
            self._start_streaming()

    def _build_ui(self) -> None:
        is_user = self._role == "user"

        # Small symmetric outer gutter — the off-side push comes from
        # addStretch(), not from a giant content margin. Stretch works
        # reliably; large left/right margins were causing the bubble
        # itself to be sized too wide and overflow on narrow panels.
        self._content_layout.setContentsMargins(8, 0, 8, 0)

        if is_user:
            self._content_layout.addStretch()

        self._bubble_frame = QWidget(self._content_widget)
        self._bubble_frame.setObjectName("BubbleUser" if is_user else "BubbleAI")
        self._bubble_frame.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred
        )

        inner = QHBoxLayout(self._bubble_frame)
        inner.setContentsMargins(0, 0, 0, 0)  # QSS padding (10/14) takes over
        inner.setSpacing(0)

        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setMinimumWidth(0)
        # PlainText: respect the user's newlines (Shift+Enter) AND avoid the
        # default rich-text mode interpreting "<" / "&" / etc. as markup.
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        # Critical: align top so multi-line content renders from the top down.
        self._label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        inner.addWidget(self._label)

        self._content_layout.addWidget(self._bubble_frame)

        if not is_user:
            self._content_layout.addStretch()

    def set_content(self, text: str, streaming: bool = False) -> None:
        """Update the displayed text.

        Args:
            text: New content to display.
            streaming: If True, attach streaming cursor and begin blinking.
        """
        self._base_text = text
        if streaming:
            self._start_streaming()
        else:
            self._stop_streaming()
        self._refresh_label()

    def finish_streaming(self) -> None:
        """Remove the streaming cursor and mark bubble as complete."""
        self._stop_streaming()
        self._refresh_label()
        self.set_status("saved")

    def append_text(self, delta: str) -> None:
        """Append a streaming delta chunk to the displayed text.

        Args:
            delta: Text chunk to append.
        """
        self._base_text += delta
        self._refresh_label()

    def _start_streaming(self) -> None:
        self._streaming = True
        self._cursor_visible = True
        if not self._blink_timer.isActive():
            self._blink_timer.start()

    def _stop_streaming(self) -> None:
        self._streaming = False
        self._cursor_visible = False
        self._blink_timer.stop()

    def _toggle_cursor(self) -> None:
        if not self._streaming:
            self._blink_timer.stop()
            return
        self._cursor_visible = not self._cursor_visible
        self._refresh_label()

    def _refresh_label(self) -> None:
        if self._streaming and self._cursor_visible:
            self._label.setText(self._base_text + "|")
        else:
            self._label.setText(self._base_text)

    @property
    def text(self) -> str:
        return self._base_text

    def resizeEvent(self, event: object) -> None:  # noqa: N802
        super().resizeEvent(event)  # type: ignore[arg-type]
        if self.width() > 120:
            # Bubble caps at 72% of the chat area — same proportion iMessage
            # uses; leaves a clear off-side gutter (via addStretch).
            bubble_max = max(140, int(self.width() * 0.72))
            self._bubble_frame.setMaximumWidth(bubble_max)
            # Label cap accounts for QSS padding (12 vertical / 16 horizontal)
            # — total horizontal is 32px.
            self._label.setMaximumWidth(max(80, bubble_max - 36))
