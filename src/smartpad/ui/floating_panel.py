"""Floating panel UI — SPEC.md sections 9, 12, 17.

FloatingPanel is the main capture surface: a frameless, always-on-top,
translucent window with a chat stream and input box.

Phase 06 implements:
- Window chrome (frameless, always-on-top, translucent bg)
- Header with drag + title + close button
- Chat stream (QScrollArea with VBox of simple text bubbles)
- Input (QTextEdit, Enter sends, Shift+Enter newline)
- Router integration (core/router.route)
- Provider chat via WorkerPool (OpenAICompatibleProvider if configured)
- Show/hide with 150ms opacity fade
- Hide on Esc, click-outside, and hotkey toggle
- Status bar
- Draggable header
- Position/size saved to settings
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from loguru import logger
from PyQt6.QtCore import (
    QEvent,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtSlot,
)
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from smartpad.config import SmartPadSettings, load_settings
from smartpad.core.router import ActionKind, route
from smartpad.core.worker_pool import WorkerPool
from smartpad.providers.base import ChatChunk, ChatMessage

# Module-level settings singleton to avoid re-instantiation during GC
_settings: SmartPadSettings | None = None


def _get_settings() -> SmartPadSettings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


# ── Minimal bubble widget used in Phase 06 ────────────────────────────────────
# Full bubble widgets arrive in Phase 07; for now every message is a text
# label styled with one of the bubble QSS IDs.

class _SimpleBubble(QFrame):
    """A minimal bubble: coloured frame + wrapping label."""

    def __init__(
        self,
        text: str,
        object_name: str,
        align_right: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self._align_right = align_right

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._label = QLabel(text)
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        if align_right:
            layout.addStretch()
        layout.addWidget(self._label)
        if not align_right:
            layout.addStretch()

    def set_text(self, text: str) -> None:
        self._label.setText(text)

    def append_text(self, delta: str) -> None:
        self._label.setText(self._label.text() + delta)


# ── Main panel ────────────────────────────────────────────────────────────────

class FloatingPanel(QWidget):
    """Frameless floating panel — the primary SmartPad UI surface."""

    def __init__(self, pool: WorkerPool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = pool
        self._settings = _get_settings()
        self._drag_pos: QPoint | None = None
        self._pending_jobs: dict[str, _SimpleBubble] = {}  # job_id → bubble
        self._chat_history: list[ChatMessage] = []

        self._build_window()
        self._build_ui()
        self._apply_geometry()
        self._connect_pool()

        # Install event filter on application to detect click-outside
        QApplication.instance().installEventFilter(self)  # type: ignore[union-attr]

    # ── Window setup ──────────────────────────────────────────────────────────

    def _build_window(self) -> None:
        self.setObjectName("FloatingPanel")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # avoids taskbar entry on most platforms
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(300, 400)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_chat_area(), stretch=1)
        root.addWidget(self._build_input_area())
        root.addWidget(self._build_status_bar())

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("PanelHeader")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        title = QLabel("SmartPad")
        title.setObjectName("HeaderTitle")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(QSize(28, 28))
        close_btn.clicked.connect(self.hide_panel)
        close_btn.setToolTip("Close panel")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(close_btn)

        # Make the header draggable
        header.mousePressEvent = self._header_mouse_press       # type: ignore[method-assign]
        header.mouseMoveEvent = self._header_mouse_move         # type: ignore[method-assign]
        header.mouseReleaseEvent = self._header_mouse_release   # type: ignore[method-assign]

        return header

    def _build_chat_area(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setObjectName("ChatScrollArea")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self._chat_container = QWidget()
        self._chat_container.setObjectName("ChatContainer")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(0, 8, 0, 8)
        self._chat_layout.setSpacing(4)
        self._chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Spacer so bubbles hug top
        self._chat_layout.addStretch()

        self._scroll.setWidget(self._chat_container)
        return self._scroll

    def _build_input_area(self) -> QWidget:
        area = QWidget()
        area.setObjectName("InputArea")

        layout = QHBoxLayout(area)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._input = QTextEdit()
        self._input.setObjectName("MessageInput")
        self._input.setPlaceholderText("Ask anything…")
        self._input.setFixedHeight(60)
        self._input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._input.installEventFilter(self)

        send_btn = QPushButton("Send")
        send_btn.setObjectName("SendButton")
        send_btn.setFixedHeight(36)
        send_btn.clicked.connect(self._on_send)

        layout.addWidget(self._input)
        layout.addWidget(send_btn)
        return area

    def _build_status_bar(self) -> QLabel:
        self._status = QLabel("Ready")
        self._status.setObjectName("StatusBar")
        self._status.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        return self._status

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _apply_geometry(self) -> None:
        s = self._settings
        w = s.panel_width
        h = s.panel_height

        if s.panel_position_x == -1:
            # Default: top-right, 80px from top, 60px from right
            screen = QApplication.primaryScreen()
            if screen is not None:
                avail = screen.availableGeometry()
                x = avail.right() - w - 60
                y = avail.top() + 80
            else:
                x, y = 100, 80
        else:
            x = s.panel_position_x
            y = s.panel_position_y

        self.setGeometry(x, y, w, h)

    def _save_geometry(self) -> None:
        geo = self.geometry()
        self._settings.panel_position_x = geo.x()
        self._settings.panel_position_y = geo.y()
        self._settings.panel_width = geo.width()
        self._settings.panel_height = geo.height()
        try:
            self._settings.save()
        except Exception as exc:
            logger.warning("Could not save panel geometry: {}", exc)

    # ── Show / Hide with fade animation ───────────────────────────────────────

    def show_panel(self) -> None:
        """Show the panel with a 150ms opacity fade."""
        if self.isVisible():
            self.activateWindow()
            self._input.setFocus()
            return

        self.setWindowOpacity(0.0)
        self.show()
        self.activateWindow()
        self._input.setFocus()

        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(150)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
        # Keep reference alive
        self._show_anim = anim

    def hide_panel(self) -> None:
        """Hide the panel with a 150ms opacity fade."""
        if not self.isVisible():
            return

        self._save_geometry()

        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(150)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.finished.connect(self.hide)
        anim.start()
        self._hide_anim = anim

    def toggle_panel(self) -> None:
        """Toggle show/hide (called from hotkey)."""
        if self.isVisible():
            self.hide_panel()
        else:
            self.show_panel()

    # ── Event handling ────────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide_panel()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj: Any, event: Any) -> bool:
        # Intercept Enter/Shift+Enter in the input box
        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter: insert newline
                    return False
                self._on_send()
                return True

        # Click outside the panel → hide
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and self.isVisible()
        ):
            try:
                gpos = event.globalPosition().toPoint()
                if not self.geometry().contains(gpos):
                    self.hide_panel()
            except AttributeError:
                pass  # event without globalPosition (e.g. tablet events)

        return False

    # ── Drag via header ───────────────────────────────────────────────────────

    def _header_mouse_press(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _header_mouse_move(self, event: Any) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _header_mouse_release(self, event: Any) -> None:
        self._drag_pos = None

    # ── Send / routing ────────────────────────────────────────────────────────

    @pyqtSlot()
    def _on_send(self) -> None:
        text = self._input.toPlainText().strip()
        if not text:
            return

        self._input.clear()

        # Show user bubble immediately (optimistic UI)
        self._add_bubble(text, "BubbleUser", align_right=True)

        # Route the text
        result = route(text)
        logger.debug("Route result: {} → {}", text[:40], result.action)

        match result.action:
            case ActionKind.CHAT:
                self._chat_history.append(ChatMessage(role="user", content=result.body))
                self._start_chat(result.body)
            case ActionKind.SAVE_NOTE:
                self._add_bubble(f"Note saved: {result.body}", "BubbleNote")
                self._set_status("Note saved")
            case ActionKind.SAVE_TASK:
                self._add_bubble(f"Task saved: {result.body}", "BubbleTask")
                self._set_status("Task saved")
            case ActionKind.SAVE_REMINDER:
                self._add_bubble(f"Reminder set: {result.body}", "BubbleReminder")
                self._set_status("Reminder set")
            case ActionKind.SAVE_SNIPPET:
                self._add_bubble(result.body, "BubbleSnippet")
                self._set_status("Snippet saved")
            case ActionKind.APP_COMMAND:
                app_action = result.metadata.get("app_action", "unknown")
                self._add_bubble(
                    f"Command: /{app_action} (not yet implemented)",
                    "BubbleAI",
                )
            case ActionKind.QUERY_DB:
                self._add_bubble(
                    "Personal-data queries not yet connected to DB.",
                    "BubbleAI",
                )
            case ActionKind.CALCULATOR:
                self._add_bubble(f"Calc: {result.body}", "BubbleAI")
            case _:
                self._chat_history.append(ChatMessage(role="user", content=result.body))
                self._start_chat(result.body)

    def _start_chat(self, text: str) -> None:
        """Build provider and stream response via worker pool."""
        provider = self._get_provider()
        if provider is None:
            self._add_bubble(
                "No provider configured. Set SMARTPAD_OPENAI_BASE_URL and "
                "SMARTPAD_OPENAI_API_KEY (or configure a provider in settings).",
                "BubbleError",
            )
            self._set_status("No provider configured")
            return

        # AI bubble placeholder — will be filled as chunks arrive
        ai_bubble = self._add_bubble("", "BubbleAI")
        self._set_status("Thinking…")

        messages = list(self._chat_history)
        job_id = str(uuid.uuid4())
        self._pending_jobs[job_id] = ai_bubble

        model = os.environ.get("SMARTPAD_OPENAI_MODEL", "gpt-3.5-turbo")

        async def _stream_to_list() -> list[ChatChunk]:
            """Collect all chunks and return them so WorkerPool can emit result."""
            chunks: list[ChatChunk] = []
            async for chunk in await provider.chat(
                messages=messages,
                model=model,
                temperature=self._settings.chat_temperature,
                stream=True,
            ):
                chunks.append(chunk)
                # We can't safely call Qt from the worker thread directly, so
                # we accumulate and emit the full list; streaming in-place is
                # wired properly in Phase 07 with a custom QRunnable.
            return chunks

        self._pool.submit_high(_stream_to_list(), job_id=job_id)

    def _get_provider(self) -> Any:
        """Instantiate OpenAICompatibleProvider from env/settings if possible."""
        from smartpad.providers.openai_compatible import OpenAICompatibleProvider  # noqa: PLC0415

        base_url = os.environ.get(
            "SMARTPAD_OPENAI_BASE_URL",
            getattr(self._settings, "openai_base_url", "") or "",
        )
        api_key = os.environ.get(
            "SMARTPAD_OPENAI_API_KEY",
            getattr(self._settings, "openai_api_key", "") or "",
        )

        if not base_url:
            return None

        return OpenAICompatibleProvider(
            base_url=base_url,
            api_key=api_key or None,
            name="openai",
        )

    # ── Worker pool callbacks ─────────────────────────────────────────────────

    def _connect_pool(self) -> None:
        self._pool.result_ready.connect(self._on_job_result)
        self._pool.error_occurred.connect(self._on_job_error)

    @pyqtSlot(str, object)
    def _on_job_result(self, job_id: str, result: Any) -> None:
        bubble = self._pending_jobs.pop(job_id, None)
        if bubble is None:
            return

        if isinstance(result, list):
            # Streaming chunks list from _stream_to_list
            full_text = "".join(c.delta for c in result if isinstance(c, ChatChunk))
            bubble.set_text(full_text)
            self._chat_history.append(
                ChatMessage(role="assistant", content=full_text)
            )
        else:
            bubble.set_text(str(result))

        self._set_status("Ready")
        self._scroll_to_bottom()

    @pyqtSlot(str, object)
    def _on_job_error(self, job_id: str, exc: Any) -> None:
        bubble = self._pending_jobs.pop(job_id, None)
        if bubble is not None:
            bubble.set_text(f"Error: {exc}")
            bubble.setObjectName("BubbleError")
        else:
            self._add_bubble(f"Error: {exc}", "BubbleError")

        self._set_status("Error")
        logger.error("Worker job {} failed: {}", job_id, exc)

    # ── Bubble helpers ────────────────────────────────────────────────────────

    def _add_bubble(
        self,
        text: str,
        object_name: str,
        align_right: bool = False,
    ) -> _SimpleBubble:
        bubble = _SimpleBubble(text, object_name, align_right=align_right)
        # Insert before the trailing stretch
        count = self._chat_layout.count()
        self._chat_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(0, self._scroll_to_bottom)
        return bubble

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _set_status(self, text: str) -> None:
        self._status.setText(text)
