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

from PyQt6.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
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

    # Emitted when the user clicks the regenerate (↻) action on an AI bubble.
    regenerate_requested = pyqtSignal()
    copied = pyqtSignal()  # tiny signal so the panel can flash a "Copied" status

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
            # Action overlay (copy + regenerate) — AI bubbles only
            self._build_action_overlay()

    def _build_action_overlay(self) -> None:
        """Hover-revealed bar with 📋 Copy and ↻ Regenerate (top-right of bubble)."""
        self._actions = QWidget(self._bubble_frame)
        self._actions.setObjectName("BubbleActionBar")
        self._actions.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row = QHBoxLayout(self._actions)
        row.setContentsMargins(2, 2, 2, 2)
        row.setSpacing(0)

        copy_btn = QPushButton("⧉")
        copy_btn.setObjectName("BubbleActionBtn")
        copy_btn.setToolTip("Copy")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setFixedSize(22, 22)
        copy_btn.clicked.connect(self._on_copy)
        row.addWidget(copy_btn)

        regen_btn = QPushButton("↻")
        regen_btn.setObjectName("BubbleActionBtn")
        regen_btn.setToolTip("Regenerate")
        regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        regen_btn.setFixedSize(22, 22)
        regen_btn.clicked.connect(self.regenerate_requested.emit)
        row.addWidget(regen_btn)

        self._actions.adjustSize()
        self._actions.hide()
        # Track hover via event filter on the bubble frame
        self._bubble_frame.installEventFilter(self)
        self._bubble_frame.setMouseTracking(True)

    def _on_copy(self) -> None:
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(self._base_text)
        self.copied.emit()

    def _reposition_actions(self) -> None:
        if not hasattr(self, "_actions"):
            return
        bw = self._bubble_frame.width()
        # Anchor to the top-right corner, slightly above the bubble
        self._actions.adjustSize()
        x = max(0, bw - self._actions.width() - 4)
        y = -self._actions.height() // 2 + 6
        self._actions.move(x, y)
        self._actions.raise_()

    def eventFilter(self, obj: object, event: object) -> bool:  # noqa: N802
        if obj is self._bubble_frame and hasattr(self, "_actions"):
            t = event.type()  # type: ignore[union-attr]
            if t == QEvent.Type.Enter:
                self._reposition_actions()
                self._actions.show()
            elif t == QEvent.Type.Leave:
                self._actions.hide()
        return super().eventFilter(obj, event)  # type: ignore[arg-type]

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
        # Re-size the bubble to match the new content (text-fit + wrap).
        self._fit_label_to_content()

    @property
    def text(self) -> str:
        return self._base_text

    def resizeEvent(self, event: object) -> None:  # noqa: N802
        super().resizeEvent(event)  # type: ignore[arg-type]
        self._fit_label_to_content()
        if hasattr(self, "_actions") and self._actions.isVisible():
            self._reposition_actions()

    def showEvent(self, event: object) -> None:  # noqa: N802
        super().showEvent(event)  # type: ignore[arg-type]
        # Re-measure once the widget is on-screen — by now the QSS font is
        # actually applied and QFontMetrics returns correct widths.
        QTimer.singleShot(0, self._fit_label_to_content)

    def _fit_label_to_content(self) -> None:
        """Size the bubble to its text — shrink for short messages, wrap for
        long ones. Uses QFontMetrics to find the natural unwrapped width and
        chooses between fit-to-content vs fixed-max-with-wrap.

        QFontMetrics can under-estimate when called before QSS has applied
        the actual font (especially during construction), so we add a
        generous buffer to avoid the "vertical sliver" failure mode where
        a 2-char message gets force-wrapped to one char per line.
        """
        if self.width() <= 120:
            return
        bubble_max = max(140, int(self.width() * 0.72))
        self._bubble_frame.setMaximumWidth(bubble_max)
        label_max = max(80, bubble_max - 30)  # 13px QSS padding × 2 + 4px slack

        fm = QFontMetrics(self._label.font())
        text = self._base_text or " "
        longest = 0
        for line in text.split("\n"):
            # boundingRect is more accurate than horizontalAdvance for the
            # actual rendered glyph width, including italics + accents.
            br = fm.boundingRect(line)
            if br.width() > longest:
                longest = br.width()

        # Generous buffer: 20px guaranteed + 15% of measured width.
        # Compensates for font-substitution differences between QFontMetrics
        # at __init__ time vs the QSS font that's actually rendered.
        buffered = int(longest * 1.15) + 20

        if buffered <= label_max:
            target = max(60, buffered)  # never narrower than 60px
            self._label.setMaximumWidth(target)
            self._label.setFixedWidth(target)
            hfw = self._label.heightForWidth(target)
            if hfw > 0:
                self._label.setMinimumHeight(hfw)
        else:
            # Long enough to need wrapping — pin at the max.
            self._label.setMaximumWidth(label_max)
            self._label.setFixedWidth(label_max)
            hfw = self._label.heightForWidth(label_max)
            if hfw > 0:
                self._label.setMinimumHeight(hfw)
