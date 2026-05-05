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

Phase 07 adds:
- Proper typed bubble widgets (ChatBubble, NoteBubble, TaskBubble,
  ReminderBubble, SnippetBubble, ErrorBubble) replacing _SimpleBubble
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
from smartpad.ui.bubbles.chat_bubble import ChatBubble
from smartpad.ui.bubbles.error_bubble import ErrorBubble
from smartpad.ui.bubbles.note_bubble import NoteBubble
from smartpad.ui.bubbles.reminder_bubble import ReminderBubble
from smartpad.ui.bubbles.snippet_bubble import SnippetBubble
from smartpad.ui.bubbles.task_bubble import TaskBubble
from smartpad.ui.slash_menu import SlashMenu  # noqa: F401 — imported for side-effects / future use

# Module-level settings singleton to avoid re-instantiation during GC
_settings: SmartPadSettings | None = None


def _get_settings() -> SmartPadSettings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


# ── Main panel ────────────────────────────────────────────────────────────────


class FloatingPanel(QWidget):
    """Frameless floating panel — the primary SmartPad UI surface."""

    def __init__(self, pool: WorkerPool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = pool
        self._settings = _get_settings()
        self._drag_pos: QPoint | None = None
        # job_id → ChatBubble (AI placeholder while streaming)
        self._pending_jobs: dict[str, ChatBubble] = {}
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

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.setFixedSize(QSize(28, 28))
        settings_btn.clicked.connect(self._open_settings)
        settings_btn.setToolTip("Settings")

        browse_btn = QPushButton("☰")
        browse_btn.setObjectName("BrowseButton")
        browse_btn.setFixedSize(QSize(28, 28))
        browse_btn.clicked.connect(self._open_browse)
        browse_btn.setToolTip("Notes & Tasks")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(QSize(28, 28))
        close_btn.clicked.connect(self.hide_panel)
        close_btn.setToolTip("Close panel")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(settings_btn)
        layout.addWidget(browse_btn)
        layout.addWidget(close_btn)

        # Make the header draggable
        header.mousePressEvent = self._header_mouse_press  # type: ignore[method-assign]
        header.mouseMoveEvent = self._header_mouse_move  # type: ignore[method-assign]
        header.mouseReleaseEvent = self._header_mouse_release  # type: ignore[method-assign]

        return header

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        from smartpad.ui.settings_dialog import SettingsDialog  # noqa: PLC0415

        dlg = SettingsDialog(parent=self)
        dlg.exec()

    def _open_browse(self) -> None:
        """Open the browse window."""
        from smartpad.ui.browse_window import BrowseWindow  # noqa: PLC0415

        dlg = BrowseWindow(parent=self)
        dlg.exec()

    def _build_chat_area(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setObjectName("ChatScrollArea")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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
        self._input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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

    @pyqtSlot()
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
        if event.type() == QEvent.Type.MouseButtonPress and self.isVisible():
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
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

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
        self._add_widget(ChatBubble(role="user", text=text))

        # Route the text
        result = route(text)
        logger.debug("Route result: {} → {}", text[:40], result.action)

        match result.action:
            case ActionKind.CHAT:
                self._chat_history.append(ChatMessage(role="user", content=result.body))
                self._start_chat(result.body)
            case ActionKind.SAVE_NOTE:
                note = NoteBubble(
                    content=result.body,
                    original_content=result.body,
                )
                note.set_status("saved")
                self._add_widget(note)
                self._set_status("Note saved")
                self._save_note_to_db(result.body)
            case ActionKind.SAVE_TASK:
                task = TaskBubble(
                    task_id=str(uuid.uuid4()),
                    content=result.body,
                )
                task.set_status("saved")
                self._add_widget(task)
                self._set_status("Task saved")
                self._save_task_to_db(result.body)
            case ActionKind.SAVE_REMINDER:
                reminder = ReminderBubble(content=result.body)
                reminder.set_status("saved")
                self._add_widget(reminder)
                self._set_status("Reminder set")
                self._save_reminder_to_db(result.body)
            case ActionKind.SAVE_SNIPPET:
                snippet = SnippetBubble(content=result.body)
                snippet.set_status("saved")
                self._add_widget(snippet)
                self._set_status("Snippet saved")
                self._save_snippet_to_db(result.body)
            case ActionKind.APP_COMMAND:
                app_action = result.metadata.get("app_action", "")
                if app_action == "settings":
                    self._open_settings()
                elif app_action in ("browse", "notes", "snippets"):
                    self._open_browse()
                else:
                    self._add_widget(
                        ChatBubble(
                            role="assistant",
                            text=f"/{app_action} — use the buttons in the header.",
                        )
                    )
            case ActionKind.QUERY_DB:
                ai_bubble = ChatBubble(
                    role="assistant",
                    text="Personal-data queries not yet connected to DB.",
                )
                ai_bubble.set_status("saved")
                self._add_widget(ai_bubble)
            case ActionKind.CALCULATOR:
                ai_bubble = ChatBubble(role="assistant", text=f"Calc: {result.body}")
                ai_bubble.set_status("saved")
                self._add_widget(ai_bubble)
            case _:
                self._chat_history.append(ChatMessage(role="user", content=result.body))
                self._start_chat(result.body)

    def _start_chat(self, text: str) -> None:
        """Build provider and stream response via worker pool."""
        provider = self._get_provider()
        if provider is None:
            err_bubble = ErrorBubble(
                message=(
                    "No provider configured. Set SMARTPAD_OPENAI_BASE_URL and "
                    "SMARTPAD_OPENAI_API_KEY (or configure a provider in settings)."
                )
            )
            self._add_widget(err_bubble)
            self._set_status("No provider configured")
            return

        # AI bubble placeholder — will be filled as chunks arrive
        ai_bubble = ChatBubble(role="assistant", text="", streaming=True)
        self._add_widget(ai_bubble)
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
            return chunks

        self._pool.submit_high(_stream_to_list(), job_id=job_id)

    def _get_provider(self) -> Any:
        """Instantiate an AI provider, checking keyring first then env vars."""
        import keyring  # noqa: PLC0415

        _SVC = "smartpad"

        def _kr(key: str) -> str:
            """Read from keyring, returning '' on any error (incl. no backend)."""
            try:
                return keyring.get_password(_SVC, key) or ""
            except Exception:
                return ""

        # Check which keys are available (keyring first, then env vars)
        anthropic_key = _kr("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
        openai_key = _kr("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
        openai_url = (
            _kr("openai_base_url")
            or os.environ.get("OPENAI_BASE_URL", "")
            or os.environ.get("SMARTPAD_OPENAI_BASE_URL", "")
        )
        google_key = _kr("google_api_key") or os.environ.get("GOOGLE_API_KEY", "")
        local_url = _kr("local_server_url") or os.environ.get("LOCAL_SERVER_URL", "")
        preferred = _kr("preferred_provider")

        # Honor explicit preference first
        if preferred == "anthropic" and anthropic_key:
            from smartpad.providers.anthropic import AnthropicProvider  # noqa: PLC0415

            return AnthropicProvider(api_key=anthropic_key)
        if preferred == "google" and google_key:
            from smartpad.providers.google import GoogleProvider  # noqa: PLC0415

            return GoogleProvider(api_key=google_key)
        if preferred in ("openai", "openai_compatible") and (openai_key or openai_url):
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=openai_url or "https://api.openai.com/v1",
                api_key=openai_key or None,
                name="openai",
            )
        if preferred == "local" and local_url:
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=local_url, api_key=None, name="local"
            )

        # Fall back: first available key wins
        if anthropic_key:
            from smartpad.providers.anthropic import AnthropicProvider  # noqa: PLC0415

            return AnthropicProvider(api_key=anthropic_key)
        if openai_key or openai_url:
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=openai_url or "https://api.openai.com/v1",
                api_key=openai_key or None,
                name="openai",
            )
        if google_key:
            from smartpad.providers.google import GoogleProvider  # noqa: PLC0415

            return GoogleProvider(api_key=google_key)
        if local_url:
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=local_url, api_key=None, name="local"
            )
        return None

    # ── DB save helpers (fire-and-forget background threads) ──────────────────

    def _save_note_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Note  # noqa: PLC0415
                from smartpad.db.repositories.notes import NotesRepo  # noqa: PLC0415

                async with get_async_session() as s:
                    await NotesRepo(s).save(
                        Note(
                            id=str(_uuid.uuid4()),
                            content=content,
                            original_content=content,
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB note save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

    def _save_task_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Task  # noqa: PLC0415
                from smartpad.db.repositories.tasks import TasksRepo  # noqa: PLC0415

                async with get_async_session() as s:
                    await TasksRepo(s).save(
                        Task(
                            id=str(_uuid.uuid4()),
                            content=content,
                            status="todo",
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB task save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

    def _save_reminder_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime, timedelta  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Reminder  # noqa: PLC0415
                from smartpad.db.repositories.reminders import RemindersRepo  # noqa: PLC0415

                # Try to parse a time from the content; fall back to 1 hour from now
                trigger_at: datetime | None = None
                try:
                    import dateparser  # noqa: PLC0415

                    parsed = dateparser.parse(content, settings={"PREFER_DATES_FROM": "future"})
                    if parsed is not None:
                        trigger_at = parsed.astimezone(UTC)
                except Exception:
                    pass
                if trigger_at is None:
                    trigger_at = datetime.now(UTC) + timedelta(hours=1)

                async with get_async_session() as s:
                    await RemindersRepo(s).save(
                        Reminder(
                            id=str(_uuid.uuid4()),
                            content=content,
                            trigger_at=trigger_at,
                            notified=False,
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB reminder save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

    def _save_snippet_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Snippet  # noqa: PLC0415
                from smartpad.db.repositories.snippets import SnippetsRepo  # noqa: PLC0415

                async with get_async_session() as s:
                    await SnippetsRepo(s).save(
                        Snippet(
                            id=str(_uuid.uuid4()),
                            content=content,
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB snippet save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

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
            bubble.set_content(full_text)
            bubble.finish_streaming()
            self._chat_history.append(ChatMessage(role="assistant", content=full_text))
        else:
            bubble.set_content(str(result))
            bubble.finish_streaming()

        self._set_status("Ready")
        self._scroll_to_bottom()

    @pyqtSlot(str, object)
    def _on_job_error(self, job_id: str, exc: Any) -> None:
        pending_bubble = self._pending_jobs.pop(job_id, None)
        if pending_bubble is not None:
            idx = self._chat_layout.indexOf(pending_bubble)
            if idx >= 0:
                self._chat_layout.removeWidget(pending_bubble)
                pending_bubble.deleteLater()
        self._add_widget(ErrorBubble(message=f"Error: {exc}"))
        self._set_status("Error")
        logger.error("Worker job {} failed: {}", job_id, exc)

    # ── Bubble helpers ────────────────────────────────────────────────────────

    def _add_widget(self, widget: QWidget) -> QWidget:
        """Insert a bubble widget before the trailing stretch.

        Args:
            widget: Any QWidget (typically a bubble subclass).

        Returns:
            The same widget for chaining.
        """
        count = self._chat_layout.count()
        self._chat_layout.insertWidget(count - 1, widget)
        QTimer.singleShot(0, self._scroll_to_bottom)
        return widget

    # Legacy helper kept for backward-compat with existing tests that call
    # _add_bubble() directly.
    def _add_bubble(
        self,
        text: str,
        object_name: str,
        align_right: bool = False,
    ) -> ChatBubble:
        """Backward-compatible wrapper — creates a ChatBubble.

        Args:
            text: Message text.
            object_name: QSS object name (used to guess role).
            align_right: If ``True``, use ``role='user'`` (right-aligned).

        Returns:
            The created ChatBubble.
        """
        role = "user" if align_right or object_name == "BubbleUser" else "assistant"
        bubble = ChatBubble(role=role, text=text)
        self._add_widget(bubble)
        return bubble

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _set_status(self, text: str) -> None:
        self._status.setText(text)
